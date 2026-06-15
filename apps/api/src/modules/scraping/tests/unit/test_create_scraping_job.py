"""Testes do comportamento do caso de uso CreateScrapingJob."""

import pytest

from apps.api.src.modules.scraping.application.ports import TaskDispatcher
from apps.api.src.modules.scraping.application.unit_of_work import ScrapingUnitOfWork
from apps.api.src.modules.scraping.application.use_cases.create_scraping_job import (
    CreateScrapingJob,
)
from apps.api.src.modules.scraping.domain.enums import JobStatus
from apps.api.src.modules.scraping.domain.exceptions import TaskDispatchError
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
    """Unit of Work minima para testar persistencia do estado do job."""

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


class FailingDispatcher(TaskDispatcher):
    """Simula uma fila indisponivel depois que o job foi persistido."""

    async def dispatch(self, job_id) -> None:
        raise TaskDispatchError("Fila indisponivel.")


@pytest.mark.anyio
async def test_dispatch_failure_is_persisted_on_job() -> None:
    """Job deve registrar falha quando nao consegue chegar ao worker."""

    jobs = InMemoryScrapingJobRepository()
    attempts = InMemoryScrapingAttemptRepository()
    results = InMemoryScrapingResultRepository()
    use_case = CreateScrapingJob(
        unit_of_work_factory=lambda: InMemoryUnitOfWork(jobs, attempts, results),
        task_dispatcher=FailingDispatcher(),
    )

    with pytest.raises(TaskDispatchError):
        await use_case.execute("https://example.com")

    persisted_jobs = list(jobs._jobs.values())
    assert len(persisted_jobs) == 1
    assert persisted_jobs[0].status is JobStatus.FAILED
    assert persisted_jobs[0].error_message == "Fila indisponivel."
