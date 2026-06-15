"""Testes do adaptador Gemini para validacao semantica estruturada."""

import json

import httpx
import pytest

from apps.api.src.modules.scraping.application.dto import (
    DeterministicValidationResult,
    SemanticValidationInput,
)
from apps.api.src.modules.scraping.domain.enums import SemanticReviewDecision
from apps.api.src.modules.scraping.domain.exceptions import SemanticValidationError
from apps.api.src.modules.scraping.infrastructure.semantic_validators.gemini_semantic_validator import (
    GeminiSemanticValidator,
)


def make_input(raw_text: str = "Conteudo ambiguo sobre uma plataforma.") -> SemanticValidationInput:
    return SemanticValidationInput(
        url="https://example.com",
        title="Startup",
        raw_text=raw_text,
        deterministic=DeterministicValidationResult(
            technical_score=1.0,
            text_score=0.80,
            evidence_score=0.30,
            quality_score=0.62,
            warnings={"no_capability_description"},
        ),
    )


def make_client_factory(handler):
    def factory() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    return factory


def valid_semantic_json() -> str:
    return json.dumps(
        {
            "startup_match_score": 0.90,
            "evidence_clarity_score": 0.80,
            "source_reliability_score": 0.70,
            "statement_specificity_score": 0.60,
            "context_completeness_score": 0.50,
            "contradiction_detected": False,
            "decision": "accepted",
            "reason": "O texto descreve um produto de IA.",
        }
    )


@pytest.mark.anyio
async def test_sends_structured_request_and_maps_valid_response() -> None:
    captured_request = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": valid_semantic_json()}]}}
                ]
            },
        )

    validator = GeminiSemanticValidator(
        api_key="secret",
        model="gemini-test",
        client_factory=make_client_factory(handler),
    )

    assessment = await validator.validate(make_input())

    assert assessment.decision is SemanticReviewDecision.ACCEPTED
    assert assessment.startup_match_score == 0.90
    assert captured_request.headers["x-goog-api-key"] == "secret"
    assert captured_request.url.path.endswith("/gemini-test:generateContent")

    body = json.loads(captured_request.content)
    generation_config = body["generationConfig"]
    assert generation_config["responseMimeType"] == "application/json"
    assert "responseJsonSchema" in generation_config
    assert body["generationConfig"]["temperature"] == 0


@pytest.mark.anyio
async def test_limits_text_sent_to_gemini() -> None:
    captured_body = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": valid_semantic_json()}]}}
                ]
            },
        )

    validator = GeminiSemanticValidator(
        api_key="secret",
        model="gemini-test",
        max_text_characters=10,
        client_factory=make_client_factory(handler),
    )

    await validator.validate(make_input(raw_text="A" * 100))

    prompt = captured_body["contents"][0]["parts"][0]["text"]
    assert "A" * 10 in prompt
    assert "A" * 11 not in prompt


@pytest.mark.anyio
async def test_rejects_invalid_structured_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": '{"decision": "accepted"}'}]}}
                ]
            },
        )

    validator = GeminiSemanticValidator(
        api_key="secret",
        model="gemini-test",
        client_factory=make_client_factory(handler),
    )

    with pytest.raises(SemanticValidationError, match="invalida"):
        await validator.validate(make_input())


@pytest.mark.anyio
async def test_translates_timeout_to_known_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    validator = GeminiSemanticValidator(
        api_key="secret",
        model="gemini-test",
        timeout_seconds=2,
        client_factory=make_client_factory(handler),
    )

    with pytest.raises(SemanticValidationError, match="timeout de 2"):
        await validator.validate(make_input())
