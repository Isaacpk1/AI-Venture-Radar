"""Testes da Orchestration V2 URL ingestion."""

from types import TracebackType
from uuid import UUID, uuid4

import pytest

from apps.api.src.modules.orchestration.application.dto import (
    CreateUrlIngestionJobInput,
    ListUrlIngestionJobsInput,
)
from apps.api.src.modules.orchestration.application.ports import (
    BriefingPort,
    DocumentContentView,
    EmbeddingsPort,
    IngestionPort,
    RecommendationsPort,
    ScrapingPort,
    StartupsPort,
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
from apps.api.src.modules.orchestration.application.use_cases.list_url_ingestion_jobs import (
    ListUrlIngestionJobs,
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

    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        status: UrlIngestionJobStatus | None = None,
        source_type: str | None = None,
    ) -> tuple[list[UrlIngestionJob], int]:
        jobs = list(self.items.values())
        if status is not None:
            jobs = [job for job in jobs if job.status is status]
        if source_type:
            jobs = [job for job in jobs if job.source_type == source_type]
        jobs.sort(key=lambda job: (job.created_at, job.id), reverse=True)
        total = len(jobs)
        start = (page - 1) * page_size
        return jobs[start : start + page_size], total


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
    def __init__(
        self,
        *,
        status: StepStatus | None = None,
        content: DocumentContentView | None = None,
    ) -> None:
        self.submissions: list[tuple[UUID, str]] = []
        self.job_id = uuid4()
        self._status = status
        self._content = content

    async def submit(
        self,
        scraping_result_id: UUID,
        *,
        source_type: str = "startup_evidence",
    ) -> UUID:
        self.submissions.append((scraping_result_id, source_type))
        return self.job_id

    async def get_status(self, job_id: UUID) -> StepStatus:
        if self._status is not None:
            return self._status
        return StepStatus(
            is_done=False,
            is_failed=False,
            result_id=None,
            error_message=None,
        )

    async def get_document_content(
        self, scraping_result_id: UUID
    ) -> DocumentContentView | None:
        return self._content


class FakeEmbeddingsPort(EmbeddingsPort):
    def __init__(self, status: StepStatus | None = None) -> None:
        self._status = status

    async def submit(self, document_id: UUID) -> UUID:
        return uuid4()

    async def get_status(self, job_id: UUID) -> StepStatus:
        if self._status is not None:
            return self._status
        return StepStatus(
            is_done=False,
            is_failed=False,
            result_id=None,
            error_message=None,
        )


class FakeStartupsPort(StartupsPort):
    def __init__(self, *, startup_id: UUID | None = None) -> None:
        self.created: list[tuple[str, str]] = []
        self.attached: list[tuple[UUID, UUID, str, str | None, str | None]] = []
        self.try_extract_calls: list[UUID] = []
        self.try_classify_calls: list[UUID] = []
        self._startup_id = startup_id or uuid4()

    async def create_startup(self, *, name: str, website_url: str) -> UUID:
        self.created.append((name, website_url))
        return self._startup_id

    async def attach_evidence(
        self,
        *,
        startup_id: UUID,
        scraping_result_id: UUID,
        source_url: str,
        title: str | None,
        notes: str | None,
    ) -> None:
        self.attached.append(
            (startup_id, scraping_result_id, source_url, title, notes)
        )

    async def try_extract(self, startup_id: UUID) -> None:
        self.try_extract_calls.append(startup_id)

    async def try_classify(self, startup_id: UUID) -> None:
        self.try_classify_calls.append(startup_id)


class FakeRecommendationsPort(RecommendationsPort):
    def __init__(self, *, count: int = 0, error: Exception | None = None) -> None:
        self.calls: list[UUID] = []
        self._count = count
        self._error = error

    async def generate(self, startup_id: UUID) -> int:
        self.calls.append(startup_id)
        if self._error is not None:
            raise self._error
        return self._count


class FakeBriefingPort(BriefingPort):
    def __init__(self, *, briefing_id: UUID | None = None) -> None:
        self.calls: list[UUID] = []
        self._briefing_id = briefing_id or uuid4()

    async def generate(self, startup_id: UUID) -> UUID:
        self.calls.append(startup_id)
        return self._briefing_id


def _make_advance_use_case(
    *,
    repository: FakeUrlIngestionJobRepository,
    scraping_port: ScrapingPort | None = None,
    ingestion_port: IngestionPort | None = None,
    embeddings_port: EmbeddingsPort | None = None,
    startups_port: StartupsPort | None = None,
    recommendations_port: RecommendationsPort | None = None,
    briefing_port: BriefingPort | None = None,
) -> AdvanceUrlIngestionJob:
    return AdvanceUrlIngestionJob(
        uow_factory=lambda: FakeUoW(repository),
        scraping_port=scraping_port or FakeScrapingPort(),
        ingestion_port=ingestion_port or FakeIngestionPort(),
        embeddings_port=embeddings_port or FakeEmbeddingsPort(),
        startups_port=startups_port or FakeStartupsPort(),
        recommendations_port=recommendations_port or FakeRecommendationsPort(),
        briefing_port=briefing_port or FakeBriefingPort(),
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
    use_case = _make_advance_use_case(
        repository=repository, scraping_port=scraping_port
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
    use_case = _make_advance_use_case(
        repository=repository,
        scraping_port=FakeScrapingPort(
            StepStatus(
                is_done=True,
                is_failed=False,
                result_id=scraping_result_id,
                error_message=None,
            )
        ),
        ingestion_port=ingestion_port,
    )

    with pytest.raises(UrlIngestionStillProcessingError):
        await use_case.execute(job_id=job.id)

    assert ingestion_port.submissions == [
        (scraping_result_id, "nvidia_knowledge")
    ]
    assert repository.items[job.id].status is UrlIngestionJobStatus.INGESTING


@pytest.mark.anyio
async def test_embedding_completion_completes_directly_for_nvidia_knowledge() -> None:
    """Nao-regressao: fontes curadas (nvidia_knowledge) nunca viram 'startup'."""

    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(
        url="https://docs.nvidia.com/nim/",
        source_type="nvidia_knowledge",
    )
    job.start_scraping(uuid4())
    job.start_ingesting(scraping_result_id=uuid4(), ingestion_job_id=uuid4())
    job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
    await repository.save(job)
    startups_port = FakeStartupsPort()
    use_case = _make_advance_use_case(
        repository=repository,
        embeddings_port=FakeEmbeddingsPort(
            StepStatus(
                is_done=True, is_failed=False, result_id=None, error_message=None
            )
        ),
        startups_port=startups_port,
    )

    await use_case.execute(job_id=job.id)

    assert repository.items[job.id].status is UrlIngestionJobStatus.COMPLETED
    assert startups_port.created == []


@pytest.mark.anyio
async def test_embedding_completion_starts_analyzing_for_startup_evidence() -> None:
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(url="https://acme.example.com")
    job.start_scraping(uuid4())
    job.start_ingesting(scraping_result_id=uuid4(), ingestion_job_id=uuid4())
    job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
    await repository.save(job)
    use_case = _make_advance_use_case(
        repository=repository,
        embeddings_port=FakeEmbeddingsPort(
            StepStatus(
                is_done=True, is_failed=False, result_id=None, error_message=None
            )
        ),
    )

    with pytest.raises(UrlIngestionStillProcessingError):
        await use_case.execute(job_id=job.id)

    assert repository.items[job.id].status is UrlIngestionJobStatus.ANALYZING


@pytest.mark.anyio
async def test_analyzing_creates_startup_with_document_title_when_no_startup_id() -> (
    None
):
    scraping_result_id = uuid4()
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(url="https://acme.example.com")
    job.start_scraping(uuid4())
    job.start_ingesting(
        scraping_result_id=scraping_result_id, ingestion_job_id=uuid4()
    )
    job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
    job.start_analyzing()
    await repository.save(job)
    startups_port = FakeStartupsPort()
    recommendations_port = FakeRecommendationsPort(count=2)
    briefing_id = uuid4()
    briefing_port = FakeBriefingPort(briefing_id=briefing_id)
    use_case = _make_advance_use_case(
        repository=repository,
        ingestion_port=FakeIngestionPort(
            content=DocumentContentView(title="Acme AI", clean_text="conteudo " * 10)
        ),
        startups_port=startups_port,
        recommendations_port=recommendations_port,
        briefing_port=briefing_port,
    )

    await use_case.execute(job_id=job.id)

    saved = repository.items[job.id]
    assert saved.status is UrlIngestionJobStatus.COMPLETED
    assert startups_port.created == [("Acme AI", "https://acme.example.com")]
    assert saved.startup_id == startups_port._startup_id
    assert saved.evidence_attached is True
    assert len(startups_port.attached) == 1
    assert startups_port.try_extract_calls == [startups_port._startup_id]
    assert startups_port.try_classify_calls == [startups_port._startup_id]
    assert recommendations_port.calls == [startups_port._startup_id]
    assert briefing_port.calls == [startups_port._startup_id]
    assert saved.recommendation_count == 2
    assert saved.briefing_id == briefing_id


@pytest.mark.anyio
async def test_analyzing_uses_hostname_when_document_has_no_title() -> None:
    scraping_result_id = uuid4()
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(url="https://www.acme.example.com/about")
    job.start_scraping(uuid4())
    job.start_ingesting(
        scraping_result_id=scraping_result_id, ingestion_job_id=uuid4()
    )
    job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
    job.start_analyzing()
    await repository.save(job)
    startups_port = FakeStartupsPort()
    use_case = _make_advance_use_case(
        repository=repository,
        ingestion_port=FakeIngestionPort(
            content=DocumentContentView(title=None, clean_text="conteudo")
        ),
        startups_port=startups_port,
    )

    await use_case.execute(job_id=job.id)

    assert startups_port.created == [
        ("acme.example.com", "https://www.acme.example.com/about")
    ]


@pytest.mark.anyio
async def test_analyzing_skips_create_startup_when_startup_id_already_set() -> None:
    """Modo 'associar a startup existente': startup_id vem do input de criacao."""

    existing_startup_id = uuid4()
    scraping_result_id = uuid4()
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(
        url="https://acme.example.com", startup_id=existing_startup_id
    )
    job.start_scraping(uuid4())
    job.start_ingesting(
        scraping_result_id=scraping_result_id, ingestion_job_id=uuid4()
    )
    job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
    job.start_analyzing()
    await repository.save(job)
    startups_port = FakeStartupsPort()
    use_case = _make_advance_use_case(
        repository=repository,
        ingestion_port=FakeIngestionPort(
            content=DocumentContentView(title="Acme AI", clean_text="conteudo")
        ),
        startups_port=startups_port,
    )

    await use_case.execute(job_id=job.id)

    assert startups_port.created == []
    assert len(startups_port.attached) == 1
    assert startups_port.attached[0][0] == existing_startup_id
    assert repository.items[job.id].startup_id == existing_startup_id


@pytest.mark.anyio
async def test_analyzing_redelivery_skips_create_and_attach_but_reruns_rest() -> None:
    """Simula reentrega-por-crash: startup_id/evidence_attached ja persistidos."""

    existing_startup_id = uuid4()
    scraping_result_id = uuid4()
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(url="https://acme.example.com")
    job.start_scraping(uuid4())
    job.start_ingesting(
        scraping_result_id=scraping_result_id, ingestion_job_id=uuid4()
    )
    job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
    job.start_analyzing()
    job.link_startup(existing_startup_id)
    job.mark_evidence_attached()
    await repository.save(job)
    startups_port = FakeStartupsPort(startup_id=existing_startup_id)
    use_case = _make_advance_use_case(
        repository=repository,
        ingestion_port=FakeIngestionPort(
            content=DocumentContentView(title="Acme AI", clean_text="conteudo")
        ),
        startups_port=startups_port,
    )

    await use_case.execute(job_id=job.id)

    assert startups_port.created == []
    assert startups_port.attached == []
    assert startups_port.try_extract_calls == [existing_startup_id]
    assert startups_port.try_classify_calls == [existing_startup_id]
    assert repository.items[job.id].status is UrlIngestionJobStatus.COMPLETED


@pytest.mark.anyio
async def test_analyzing_fails_job_when_recommendations_port_raises() -> None:
    scraping_result_id = uuid4()
    repository = FakeUrlIngestionJobRepository()
    job = UrlIngestionJob(url="https://acme.example.com")
    job.start_scraping(uuid4())
    job.start_ingesting(
        scraping_result_id=scraping_result_id, ingestion_job_id=uuid4()
    )
    job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
    job.start_analyzing()
    await repository.save(job)
    use_case = _make_advance_use_case(
        repository=repository,
        ingestion_port=FakeIngestionPort(
            content=DocumentContentView(title="Acme AI", clean_text="conteudo")
        ),
        recommendations_port=FakeRecommendationsPort(
            error=RuntimeError("falha inesperada")
        ),
    )

    await use_case.execute(job_id=job.id)

    saved = repository.items[job.id]
    assert saved.status is UrlIngestionJobStatus.FAILED
    assert saved.error_message == "falha inesperada"


@pytest.mark.anyio
async def test_list_url_ingestion_jobs_filters_and_paginates_history() -> None:
    repository = FakeUrlIngestionJobRepository()
    matching = UrlIngestionJob(url="https://acme.example.com")
    matching.start_scraping(uuid4())
    other_status = UrlIngestionJob(url="https://beta.example.com")
    other_source = UrlIngestionJob(
        url="https://docs.nvidia.com/nim/", source_type="nvidia_knowledge"
    )
    other_source.start_scraping(uuid4())
    for job in (matching, other_status, other_source):
        await repository.save(job)

    page = await ListUrlIngestionJobs(lambda: FakeUoW(repository)).execute(
        ListUrlIngestionJobsInput(
            page=1,
            page_size=10,
            status=UrlIngestionJobStatus.SCRAPING,
            source_type="startup_evidence",
        )
    )

    assert page.total == 1
    assert page.items[0].id == matching.id
