"""Testes do comportamento do caso de uso ExecuteScrapingJob."""

from uuid import uuid4

import pytest

from apps.api.src.modules.scraping.application.unit_of_work import ScrapingUnitOfWork
from apps.api.src.modules.scraping.application.use_cases.execute_scraping_job import (
    ExecuteScrapingJob,
)
from apps.api.src.modules.scraping.domain.entities import ScrapingJob
from apps.api.src.modules.scraping.domain.enums import JobStatus
from apps.api.src.modules.scraping.infrastructure.repositories.in_memory_attempt_repository import (
    InMemoryScrapingAttemptRepository,
)
from apps.api.src.modules.scraping.infrastructure.repositories.in_memory_job_repository import (
    InMemoryScrapingJobRepository,
)
from apps.api.src.modules.scraping.infrastructure.repositories.in_memory_result_repository import (
    InMemoryScrapingResultRepository,
)


class InMemoryUnitOfWork(ScrapingUnitOfWork):
    """Unit of Work minima para testar o caso de uso sem PostgreSQL."""

    def __init__(self, jobs, attempts, results) -> None:
        self.job_repository = jobs
        self.attempt_repository = attempts
        self.result_repository = results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exception_type, exception, traceback) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.mark.anyio
async def test_duplicate_message_does_not_execute_completed_job() -> None:
    """Redelivery de um job terminal deve ser ignorada com seguranca."""

    jobs = InMemoryScrapingJobRepository()
    attempts = InMemoryScrapingAttemptRepository()
    results = InMemoryScrapingResultRepository()
    job = ScrapingJob(url="https://example.com")
    job.start()
    job.complete(uuid4())
    await jobs.save(job)

    pipeline_was_called = False

    def create_pipeline(attempt_repository):
        nonlocal pipeline_was_called
        pipeline_was_called = True
        raise AssertionError("A pipeline nao deveria ser criada.")

    use_case = ExecuteScrapingJob(
        unit_of_work_factory=lambda: InMemoryUnitOfWork(jobs, attempts, results),
        pipeline_factory=create_pipeline,
    )

    restored_job = await use_case.execute(job.id)

    assert restored_job.status is JobStatus.COMPLETED
    assert pipeline_was_called is False
    assert await attempts.list_by_job_id(job.id) == []
