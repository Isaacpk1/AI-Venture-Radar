"""Testes da Orchestration V2 URL ingestion."""

from types import TracebackType
from uuid import UUID, uuid4

import pytest

from apps.api.src.modules.orchestration.application.dto import (
    CreateUrlIngestionJobInput,
)
from apps.api.src.modules.orchestration.application.ports import (
    EmbeddingsPort,
    IngestionPort,
    ScrapingPort,
    StepStatus,
    UrlIngestionTaskDispatcher,
)
from apps.api.src.modules.orchestration.application.unit_of_work import (
    AnalysisUnitOfWork,
)
from apps.api.src.modules.orchestration.application.use_cases.advance_url_ingestion_job import (
    AdvanceUrlIngestionJob,
)
from apps.api.src.modules.orchestration.application.use_cases.create_url_ingestion_job import (
    CreateUrlIngestionJob,
)
from apps.api.src.modules.orchestration.domain.entities import UrlIngestionJob
from apps.api.src.modules.orchestration.domain.enums import UrlIngestionJobStatus
from apps.api.src.modules.orchestration.domain.exceptions import (
    UrlIngestionStillProcessingError,
)
from apps.api.src.modules.orchestration.domain.repositories import (
    AnalysisJobRepository,
    UrlIngestionJobRepository,
)


class EmptyAnalysisJobRepository(AnalysisJobRepository):
    async def save(self, analysis_job) -> None:
        pass

    async def get_by_id(self, analysis_job_id: UUID):
        return None

    async def list_by_startup_id(self, startup_id: UUID) -> list:
        return []


class FakeUrlIngestionJobRepository(UrlIngestionJobRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, UrlIngestionJob] = {}

    async def save(self, job: UrlIngestionJob) -> None:
        self.items[job.id] = job

    async def get_by_id(self, job_id: UUID) -> UrlIngestionJob | None:
        return self.items.get(job_id)


class FakeUoW(AnalysisUnitOfWork):
    def __init__(self, repository: FakeUrlIngestionJobRepository) -> None:
        self.analysis_job_repository = EmptyAnalysisJobRepository()
        self.url_ingestion_job_repository = repository

    async def __aenter__(self) -> "FakeUoW":
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


class FakeDispatcher(UrlIngestionTaskDispatcher):
    def __init__(self) -> None:
        self.dispatched_job_ids: list[UUID] = []

    async def dispatch(self, *, job_id: UUID) -> None:
        self.dispatched_job_ids.append(job_id)


class FakeScrapingPort(ScrapingPort):
    def __init__(self, status: StepStatus | None = None) -> None:
        self.submitted_urls: list[str] = []
        self.submitted_source_types: list[str] = []
        self.job_id = uuid4()
        self.status = status

    async def submit(self, url: str, *, source_type: str = "startup_evidence") -> UUID:
        self.submitted_urls.append(url)
        self.submitted_source_types.append(source_type)
        return self.job_id

    async def get_status(self, job_id: UUID) -> StepStatus:
        assert self.status is not None
        return self.status


class FakeIngestionPort(IngestionPort):
    def __init__(self) -> None:
        self.submissions: list[tuple[UUID, str]] = []
        self.job_id = uuid4()

    async def submit(
        self,
        scraping_result_id: UUID,
        *,
        source_type: str = "startup_evidence",
    ) -> UUID:
        self.submissions.append((scraping_result_id, source_type))
        return self.job_id

    async def get_status(self, job_id: UUID) -> StepStatus:
        return StepStatus(
            is_done=False,
            is_failed=False,
            result_id=None,
            error_message=None,
        )


class FakeEmbeddingsPort(EmbeddingsPort):
    async def submit(self, document_id: UUID) -> UUID:
        return uuid4()

    async def get_status(self, job_id: UUID) -> StepStatus:
        return StepStatus(
            is_done=False,
            is_failed=False,
            result_id=None,
            error_message=None,
        )


@pytest.mark.anyio
async def test_create_url_ingestion_job_persists_source_type_and_dispatches() -> None:
    repository = FakeUrlIngestionJobRepository()
    dispatcher = FakeDispatcher()
    use_case = CreateUrlIngestionJob(lambda: FakeUoW(repository), dispatcher)

    view = await use_case.execute(
        CreateUrlIngestionJobInput(
            url="https://docs.nvidia.com/nim/",
            source_type="nvidia_knowledge",
        )
    )

    assert view.status is UrlIngestionJobStatus.PENDING
    assert view.source_type == "nvidia_knowledge"
    assert dispatcher.dispatched_job_ids == [view.id]
    assert repository.items[view.id].source_type == "nvidia_knowledge"


@pytest.mark.anyio
async def test_advance_uses_job_source_type_when_submitting_scraping() -> None:
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(
        url="https://docs.nvidia.com/nim/",
        source_type="nvidia_knowledge",
    )
    await repository.save(job)
    scraping_port = FakeScrapingPort()
    use_case = AdvanceUrlIngestionJob(
        uow_factory=lambda: FakeUoW(repository),
        scraping_port=scraping_port,
        ingestion_port=FakeIngestionPort(),
        embeddings_port=FakeEmbeddingsPort(),
    )

    with pytest.raises(UrlIngestionStillProcessingError):
        await use_case.execute(job_id=job.id)

    assert scraping_port.submitted_urls == ["https://docs.nvidia.com/nim/"]
    assert scraping_port.submitted_source_types == ["nvidia_knowledge"]
    assert repository.items[job.id].status is UrlIngestionJobStatus.SCRAPING


@pytest.mark.anyio
async def test_advance_uses_job_source_type_when_submitting_ingestion() -> None:
    scraping_result_id = uuid4()
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(
        url="https://docs.nvidia.com/nim/",
        source_type="nvidia_knowledge",
    )
    job.start_scraping(uuid4())
    await repository.save(job)
    ingestion_port = FakeIngestionPort()
    use_case = AdvanceUrlIngestionJob(
        uow_factory=lambda: FakeUoW(repository),
        scraping_port=FakeScrapingPort(
            StepStatus(
                is_done=True,
                is_failed=False,
                result_id=scraping_result_id,
                error_message=None,
            )
        ),
        ingestion_port=ingestion_port,
        embeddings_port=FakeEmbeddingsPort(),
    )

    with pytest.raises(UrlIngestionStillProcessingError):
        await use_case.execute(job_id=job.id)

    assert ingestion_port.submissions == [
        (scraping_result_id, "nvidia_knowledge")
    ]
    assert repository.items[job.id].status is UrlIngestionJobStatus.INGESTING
