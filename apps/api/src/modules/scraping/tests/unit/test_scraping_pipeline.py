"""Testes unitários da orquestração realizada pela pipeline."""

from uuid import uuid4

import pytest

from apps.api.src.modules.scraping.application.dto import (
    DeterministicValidationResult,
    ScrapingOutput,
    SemanticAssessment,
)
from apps.api.src.modules.scraping.application.ports import (
    DeterministicValidator,
    Scraper,
    SemanticValidator,
)
from apps.api.src.modules.scraping.application.quality_scoring_service import (
    QualityScoringService,
)
from apps.api.src.modules.scraping.application.scraping_pipeline import (
    ScrapingPipeline,
)
from apps.api.src.modules.scraping.application.strategy_selector import (
    ScrapingStrategySelector,
)
from apps.api.src.modules.scraping.domain.enums import (
    AttemptStatus,
    ScrapingMethod,
    SemanticReviewDecision,
)
from apps.api.src.modules.scraping.domain.exceptions import (
    ScrapingFailedError,
    ScrapingLimitExceededError,
)
from apps.api.src.modules.scraping.domain.policies import (
    ContentAcceptancePolicy,
    FallbackPolicy,
    ValidationDecisionPolicy,
)
from apps.api.src.modules.scraping.infrastructure.repositories.in_memory_attempt_repository import (
    InMemoryScrapingAttemptRepository,
)


class FakeScraper(Scraper):
    """Scraper configurável usado para simular sucesso ou falha."""

    def __init__(
        self,
        method: ScrapingMethod,
        *,
        text: str = "conteúdo aprovado",
        error: Exception | None = None,
    ) -> None:
        self.method = method
        self.text = text
        self.error = error
        self.call_count = 0

    async def scrape(self, scraping_input) -> ScrapingOutput:
        self.call_count += 1

        if self.error is not None:
            raise self.error

        return ScrapingOutput(
            source_url=scraping_input.url,
            final_url=scraping_input.url,
            title="Startup",
            raw_html=f"<html>{self.text}</html>",
            raw_text=self.text,
            status_code=200,
            content_type="text/html",
            method=self.method,
        )


class FakeValidator(DeterministicValidator):
    """Produz validações previsíveis com base no texto simulado."""

    async def validate(self, output: ScrapingOutput) -> DeterministicValidationResult:
        if output.raw_text == "texto insuficiente":
            return DeterministicValidationResult(
                technical_score=1.0,
                text_score=0.10,
                evidence_score=0.10,
                problems={"insufficient_text"},
            )

        if output.raw_text == "conteudo ambiguo":
            return DeterministicValidationResult(
                technical_score=0.90,
                text_score=0.80,
                evidence_score=0.20,
            )

        return DeterministicValidationResult(
            technical_score=1.0,
            text_score=0.90,
            evidence_score=0.80,
        )


class FakeSemanticValidator(SemanticValidator):
    """Simula uma LLM que devolve fatores estruturados."""

    def __init__(self, *, factor_score: float = 0.90) -> None:
        self.call_count = 0
        self.factor_score = factor_score

    async def validate(self, semantic_input) -> SemanticAssessment:
        self.call_count += 1
        return SemanticAssessment(
            startup_match_score=self.factor_score,
            evidence_clarity_score=self.factor_score,
            source_reliability_score=self.factor_score,
            statement_specificity_score=self.factor_score,
            context_completeness_score=self.factor_score,
            contradiction_detected=False,
            decision=SemanticReviewDecision.ACCEPTED,
            reason="O texto descreve claramente o produto.",
        )


def make_pipeline(
    strategies: list[Scraper],
    attempt_repository: InMemoryScrapingAttemptRepository,
    semantic_validator: SemanticValidator | None = None,
) -> ScrapingPipeline:
    """Monta a pipeline com dependências controladas pelo teste."""

    return ScrapingPipeline(
        strategy_selector=ScrapingStrategySelector(strategies),
        validator=FakeValidator(),
        scoring_service=QualityScoringService(),
        decision_policy=ValidationDecisionPolicy(
            ContentAcceptancePolicy(),
            FallbackPolicy(),
        ),
        attempt_repository=attempt_repository,
        semantic_validator=semantic_validator,
    )


@pytest.mark.anyio
async def test_pipeline_accepts_first_valid_strategy() -> None:
    """Conteúdo bom encerra a pipeline sem executar a próxima estratégia."""

    attempts = InMemoryScrapingAttemptRepository()
    first = FakeScraper(ScrapingMethod.BEAUTIFULSOUP)
    second = FakeScraper(ScrapingMethod.PLAYWRIGHT)

    result = await make_pipeline([first, second], attempts).execute(
        uuid4(),
        "https://example.com",
    )

    assert result.method is ScrapingMethod.BEAUTIFULSOUP
    assert first.call_count == 1
    assert second.call_count == 0


@pytest.mark.anyio
async def test_pipeline_uses_fallback_after_low_quality_content() -> None:
    """Problema recuperável de validação deve executar a próxima estratégia."""

    attempts = InMemoryScrapingAttemptRepository()
    job_id = uuid4()
    first = FakeScraper(
        ScrapingMethod.BEAUTIFULSOUP,
        text="texto insuficiente",
    )
    second = FakeScraper(ScrapingMethod.PLAYWRIGHT)

    result = await make_pipeline([first, second], attempts).execute(
        job_id,
        "https://example.com",
    )
    saved_attempts = await attempts.list_by_job_id(job_id)

    assert result.method is ScrapingMethod.PLAYWRIGHT
    assert [attempt.status for attempt in saved_attempts] == [
        AttemptStatus.FALLBACK,
        AttemptStatus.ACCEPTED,
    ]


@pytest.mark.anyio
async def test_pipeline_uses_fallback_after_recoverable_error() -> None:
    """Erro técnico recuperável deve permitir outra tecnologia."""

    attempts = InMemoryScrapingAttemptRepository()
    first = FakeScraper(
        ScrapingMethod.BEAUTIFULSOUP,
        error=ScrapingLimitExceededError("Timeout individual."),
    )
    second = FakeScraper(ScrapingMethod.PLAYWRIGHT)

    result = await make_pipeline([first, second], attempts).execute(
        uuid4(),
        "https://example.com",
    )

    assert result.method is ScrapingMethod.PLAYWRIGHT
    assert second.call_count == 1


@pytest.mark.anyio
async def test_pipeline_propagates_unexpected_error_without_fallback() -> None:
    """Erro inesperado não pode ser escondido tentando outra estratégia."""

    attempts = InMemoryScrapingAttemptRepository()
    first = FakeScraper(
        ScrapingMethod.BEAUTIFULSOUP,
        error=RuntimeError("Bug inesperado."),
    )
    second = FakeScraper(ScrapingMethod.PLAYWRIGHT)

    with pytest.raises(RuntimeError, match="Bug inesperado"):
        await make_pipeline([first, second], attempts).execute(
            uuid4(),
            "https://example.com",
        )

    assert second.call_count == 0


@pytest.mark.anyio
async def test_pipeline_calls_semantic_validator_only_for_ambiguous_content() -> None:
    attempts = InMemoryScrapingAttemptRepository()
    semantic_validator = FakeSemanticValidator()
    scraper = FakeScraper(
        ScrapingMethod.BEAUTIFULSOUP,
        text="conteudo ambiguo",
    )

    result = await make_pipeline(
        [scraper],
        attempts,
        semantic_validator=semantic_validator,
    ).execute(uuid4(), "https://example.com")

    assert semantic_validator.call_count == 1
    assert result.metadata["semantic_reviewed"] is True
    assert result.metadata["semantic_confidence"] == 0.9


@pytest.mark.anyio
async def test_pipeline_does_not_call_semantic_validator_for_clear_content() -> None:
    attempts = InMemoryScrapingAttemptRepository()
    semantic_validator = FakeSemanticValidator()

    await make_pipeline(
        [FakeScraper(ScrapingMethod.BEAUTIFULSOUP)],
        attempts,
        semantic_validator=semantic_validator,
    ).execute(uuid4(), "https://example.com")

    assert semantic_validator.call_count == 0


@pytest.mark.anyio
async def test_pipeline_rejects_semantic_acceptance_with_low_confidence() -> None:
    attempts = InMemoryScrapingAttemptRepository()
    semantic_validator = FakeSemanticValidator(factor_score=0.60)

    with pytest.raises(ScrapingFailedError, match="rejeitado"):
        await make_pipeline(
            [
                FakeScraper(
                    ScrapingMethod.BEAUTIFULSOUP,
                    text="conteudo ambiguo",
                )
            ],
            attempts,
            semantic_validator=semantic_validator,
        ).execute(uuid4(), "https://example.com")

    assert semantic_validator.call_count == 1
