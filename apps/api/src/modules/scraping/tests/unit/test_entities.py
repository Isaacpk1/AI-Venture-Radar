"""Testes unitários das entidades do domínio de scraping."""

from uuid import uuid4

import pytest

from apps.api.src.modules.scraping.domain.entities import (
    ScrapingAttempt,
    ScrapingJob,
)
from apps.api.src.modules.scraping.domain.enums import (
    AttemptStatus,
    JobStatus,
    ScrapingMethod,
    ValidationDecision,
)
from apps.api.src.modules.scraping.domain.exceptions import (
    InvalidJobTransitionError,
)


def test_new_job_starts_pending() -> None:
    """Todo job novo deve aguardar execução."""

    job = ScrapingJob(url="https://example.com")

    assert job.status is JobStatus.PENDING
    assert job.started_at is None
    assert job.finished_at is None
    assert job.result_id is None


def test_job_can_follow_successful_lifecycle() -> None:
    """Um job pode seguir de pending para running e completed."""

    job = ScrapingJob(url="https://example.com")
    result_id = uuid4()

    job.start()
    job.complete(result_id)

    assert job.status is JobStatus.COMPLETED
    assert job.started_at is not None
    assert job.finished_at is not None
    assert job.result_id == result_id


def test_pending_job_cannot_complete_directly() -> None:
    """A entidade deve bloquear a transição pending para completed."""

    job = ScrapingJob(url="https://example.com")

    with pytest.raises(InvalidJobTransitionError):
        job.complete(uuid4())


def test_running_job_can_fail_with_reason() -> None:
    """Falhas conhecidas devem finalizar o job com uma mensagem."""

    job = ScrapingJob(url="https://example.com")

    job.start()
    job.fail("Nenhuma estratégia produziu conteúdo válido.")

    assert job.status is JobStatus.FAILED
    assert job.error_message == "Nenhuma estratégia produziu conteúdo válido."
    assert job.finished_at is not None


def test_attempt_maps_fallback_decision_to_fallback_status() -> None:
    """A decisão de fallback deve gerar o estado correspondente."""

    attempt = ScrapingAttempt(
        job_id=uuid4(),
        method=ScrapingMethod.BEAUTIFULSOUP,
    )

    attempt.finish_validation(
        decision=ValidationDecision.FALLBACK,
        technical_score=0.90,
        text_score=0.20,
        evidence_score=0.10,
        quality_score=0.37,
        problems=["insufficient_text"],
        warnings=[],
    )

    assert attempt.status is AttemptStatus.FALLBACK
    assert attempt.decision is ValidationDecision.FALLBACK
    assert attempt.quality_score == 0.37
    assert attempt.problems == ["insufficient_text"]
    assert attempt.finished_at is not None


def test_finished_attempt_cannot_fail_again() -> None:
    """Uma tentativa finalizada não pode receber outro estado final."""

    attempt = ScrapingAttempt(
        job_id=uuid4(),
        method=ScrapingMethod.BEAUTIFULSOUP,
    )
    attempt.finish_validation(
        decision=ValidationDecision.ACCEPT,
        technical_score=1.0,
        text_score=1.0,
        evidence_score=1.0,
        quality_score=1.0,
        problems=[],
        warnings=[],
    )

    with pytest.raises(InvalidJobTransitionError):
        attempt.fail("Erro tardio.")
