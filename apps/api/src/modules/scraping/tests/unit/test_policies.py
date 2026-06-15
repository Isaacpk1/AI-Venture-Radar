"""Testes unitários das políticas de decisão do domínio."""

import pytest

from apps.api.src.modules.scraping.domain.enums import ValidationDecision
from apps.api.src.modules.scraping.domain.policies import (
    ContentAcceptancePolicy,
    FallbackPolicy,
    ValidationDecisionPolicy,
    ValidationSummary,
)


@pytest.fixture
def decision_policy() -> ValidationDecisionPolicy:
    """Cria a política completa usada pelos diferentes cenários."""

    return ValidationDecisionPolicy(
        acceptance_policy=ContentAcceptancePolicy(),
        fallback_policy=FallbackPolicy(),
    )


def test_accepts_high_quality_content_without_blockers(
    decision_policy: ValidationDecisionPolicy,
) -> None:
    """Conteúdo bom deve ser aceito sem tentar outra tecnologia."""

    summary = ValidationSummary(
        technical_score=0.95,
        text_score=0.85,
        evidence_score=0.80,
        quality_score=0.85,
    )

    decision = decision_policy.decide(
        summary,
        has_next_strategy=True,
    )

    assert decision is ValidationDecision.ACCEPT


def test_blocking_problem_rejects_even_with_maximum_score(
    decision_policy: ValidationDecisionPolicy,
) -> None:
    """Um captcha bloqueia aceitação mesmo com scores altos."""

    summary = ValidationSummary(
        technical_score=1.0,
        text_score=1.0,
        evidence_score=1.0,
        quality_score=1.0,
        problems={"captcha"},
    )

    decision = decision_policy.decide(
        summary,
        has_next_strategy=True,
    )

    assert decision is ValidationDecision.REJECT


def test_recoverable_problem_uses_fallback_when_strategy_exists(
    decision_policy: ValidationDecisionPolicy,
) -> None:
    """Texto insuficiente permite tentar uma próxima tecnologia."""

    summary = ValidationSummary(
        technical_score=0.90,
        text_score=0.20,
        evidence_score=0.10,
        quality_score=0.37,
        problems={"insufficient_text"},
    )

    decision = decision_policy.decide(
        summary,
        has_next_strategy=True,
    )

    assert decision is ValidationDecision.FALLBACK


def test_recoverable_problem_rejects_without_another_strategy(
    decision_policy: ValidationDecisionPolicy,
) -> None:
    """Sem próxima tecnologia, um conteúdo ruim precisa ser rejeitado."""

    summary = ValidationSummary(
        technical_score=0.90,
        text_score=0.20,
        evidence_score=0.10,
        quality_score=0.37,
        problems={"insufficient_text"},
    )

    decision = decision_policy.decide(
        summary,
        has_next_strategy=False,
    )

    assert decision is ValidationDecision.REJECT
