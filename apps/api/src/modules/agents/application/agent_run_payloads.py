"""Conversores entre payload persistido e DTOs publicos dos agentes.

O banco guarda JSONB. Os grafos usam dataclasses tipadas. Este arquivo e o
ponto explicito de traducao entre esses dois formatos.
"""

from uuid import UUID

from apps.api.src.modules.agents.application.dto import (
    EvidenceValidationInput,
    EvidenceValidationResult,
    SearchPlanInput,
    SearchPlanResult,
    SearchQuerySuggestion,
)
from apps.api.src.modules.agents.domain.enums import AgentDecision


def _optional_uuid(value: object) -> UUID | None:
    if value in (None, ""):
        return None
    return UUID(str(value))


def evidence_validation_input_from_payload(
    payload: dict[str, object],
) -> EvidenceValidationInput:
    """Reconstrói ``EvidenceValidationInput`` a partir do JSON persistido."""

    return EvidenceValidationInput(
        url=str(payload["url"]),
        title=payload.get("title") if payload.get("title") is not None else None,
        raw_text=str(payload["raw_text"]),
        technical_score=float(payload["technical_score"]),
        text_score=float(payload["text_score"]),
        evidence_score=float(payload["evidence_score"]),
        quality_score=float(payload["quality_score"]),
        deterministic_problems=list(payload.get("deterministic_problems", [])),
        deterministic_warnings=list(payload.get("deterministic_warnings", [])),
        startup_match_score=float(payload.get("startup_match_score", 0.0)),
        evidence_clarity_score=float(payload.get("evidence_clarity_score", 0.0)),
        source_reliability_score=float(payload.get("source_reliability_score", 0.0)),
        statement_specificity_score=float(
            payload.get("statement_specificity_score", 0.0)
        ),
        context_completeness_score=float(
            payload.get("context_completeness_score", 0.0)
        ),
        contradiction_detected=bool(payload.get("contradiction_detected", False)),
        semantic_decision=str(payload.get("semantic_decision", "")),
        semantic_reason=str(payload.get("semantic_reason", "")),
        semantic_confidence=float(payload.get("semantic_confidence", 0.0)),
        startup_id=_optional_uuid(payload.get("startup_id")),
    )


def evidence_validation_result_to_payload(
    result: EvidenceValidationResult,
) -> dict[str, object]:
    """Serializa resultado de validacao de evidencia para JSON."""

    return {
        "decision": result.decision.value,
        "reason": result.reason,
    }


def search_plan_input_from_payload(payload: dict[str, object]) -> SearchPlanInput:
    """Reconstrói ``SearchPlanInput`` a partir do JSON persistido."""

    return SearchPlanInput(
        startup_name=(
            str(payload["startup_name"])
            if payload.get("startup_name") is not None
            else None
        ),
        source_url=str(payload["source_url"]),
        source_title=(
            str(payload["source_title"])
            if payload.get("source_title") is not None
            else None
        ),
        raw_text=str(payload["raw_text"]),
        reason=str(payload["reason"]),
        known_terms=[str(term) for term in payload.get("known_terms", [])],
        excluded_urls=[str(url) for url in payload.get("excluded_urls", [])],
        max_queries=int(payload.get("max_queries", 5)),
    )


def search_plan_result_to_payload(result: SearchPlanResult) -> dict[str, object]:
    """Serializa plano de busca para JSON."""

    return {
        "queries": [
            {
                "query": query.query,
                "purpose": query.purpose,
                "priority": query.priority,
            }
            for query in result.queries
        ],
        "reason": result.reason,
    }


def search_plan_result_from_payload(payload: dict[str, object]) -> SearchPlanResult:
    """Reconstrói resultado de plano de busca quando necessario em testes."""

    return SearchPlanResult(
        queries=[
            SearchQuerySuggestion(
                query=str(item["query"]),
                purpose=str(item["purpose"]),
                priority=int(item["priority"]),
            )
            for item in payload.get("queries", [])
            if isinstance(item, dict)
        ],
        reason=str(payload["reason"]),
    )


def evidence_validation_result_from_payload(
    payload: dict[str, object],
) -> EvidenceValidationResult:
    """Reconstrói resultado de validacao quando necessario em testes."""

    return EvidenceValidationResult(
        decision=AgentDecision(str(payload["decision"])),
        reason=str(payload["reason"]),
    )
