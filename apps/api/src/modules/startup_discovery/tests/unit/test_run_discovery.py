"""Testes unitarios do modulo startup_discovery."""

from types import TracebackType
from uuid import UUID, uuid4

import pytest

from apps.api.src.modules.startup_discovery.application.ports import HubLinkExtractor
from apps.api.src.modules.startup_discovery.application.use_cases.get_discovery_run import (
    GetDiscoveryRun,
)
from apps.api.src.modules.startup_discovery.application.use_cases.run_discovery import (
    RunStartupDiscovery,
)
from apps.api.src.modules.startup_discovery.domain.entities import DiscoveryRun
from apps.api.src.modules.startup_discovery.domain.enums import DiscoveryRunStatus
from apps.api.src.modules.startup_discovery.domain.exceptions import (
    DiscoveryRunNotFoundError,
)
from apps.api.src.modules.startup_discovery.domain.hub_registry import HUB_SOURCES


class FakeDiscoveryRunRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, DiscoveryRun] = {}

    async def save(self, run: DiscoveryRun) -> None:
        self.items[run.id] = run

    async def get_by_id(self, run_id: UUID) -> DiscoveryRun | None:
        return self.items.get(run_id)

    async def list_recent(self, *, limit: int = 20) -> list[DiscoveryRun]:
        all_runs = sorted(self.items.values(), key=lambda r: r.created_at, reverse=True)
        return all_runs[:limit]


class FakeUnitOfWork:
    def __init__(self, repository: FakeDiscoveryRunRepository) -> None:
        self.repository = repository
        self._committed = False

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self._committed = True


class FakeHubExtractor(HubLinkExtractor):
    def __init__(self, urls: list[str]) -> None:
        self._urls = urls

    async def extract(self, listing_url: str, *, limit: int) -> list[str]:
        return self._urls[:limit]


class FailingHubExtractor(HubLinkExtractor):
    async def extract(self, listing_url: str, *, limit: int) -> list[str]:
        raise RuntimeError("hub offline")


class FakeUrlSubmitter:
    def __init__(self) -> None:
        self.submitted: list[str] = []

    async def submit(self, url: str) -> UUID:
        self.submitted.append(url)
        return uuid4()


def make_uow_factory(repo: FakeDiscoveryRunRepository):
    def factory():
        return FakeUnitOfWork(repo)

    return factory


@pytest.mark.anyio
async def test_run_discovery_completes_with_submitted_urls():
    repo = FakeDiscoveryRunRepository()
    submitter = FakeUrlSubmitter()
    extractors = {hub.extractor_type: FakeHubExtractor([f"https://startup{i}.com" for i in range(5)]) for hub in HUB_SOURCES}

    use_case = RunStartupDiscovery(
        uow_factory=make_uow_factory(repo),
        extractors=extractors,
        url_ingestion_submitter=submitter,
        max_per_run=10,
    )

    view = await use_case.execute()

    assert view.status == DiscoveryRunStatus.COMPLETED
    assert view.jobs_submitted > 0
    assert len(submitter.submitted) > 0


@pytest.mark.anyio
async def test_run_discovery_respects_max_per_run_limit():
    repo = FakeDiscoveryRunRepository()
    submitter = FakeUrlSubmitter()
    extractors = {hub.extractor_type: FakeHubExtractor([f"https://s{i}.com" for i in range(15)]) for hub in HUB_SOURCES}

    use_case = RunStartupDiscovery(
        uow_factory=make_uow_factory(repo),
        extractors=extractors,
        url_ingestion_submitter=submitter,
        max_per_run=7,
    )

    view = await use_case.execute()

    assert len(submitter.submitted) <= 7
    assert view.jobs_submitted <= 7


@pytest.mark.anyio
async def test_run_discovery_skips_failing_hub_best_effort():
    repo = FakeDiscoveryRunRepository()
    submitter = FakeUrlSubmitter()

    hub_names = [hub.extractor_type for hub in HUB_SOURCES]
    extractors = {name: FailingHubExtractor() for name in hub_names}
    if hub_names:
        extractors[hub_names[0]] = FakeHubExtractor(["https://startupok.com"])

    use_case = RunStartupDiscovery(
        uow_factory=make_uow_factory(repo),
        extractors=extractors,
        url_ingestion_submitter=submitter,
        max_per_run=10,
    )

    view = await use_case.execute()

    assert view.status == DiscoveryRunStatus.COMPLETED
    assert len(submitter.submitted) >= 1


@pytest.mark.anyio
async def test_run_discovery_fails_when_all_hubs_fail():
    repo = FakeDiscoveryRunRepository()
    submitter = FakeUrlSubmitter()
    extractors = {hub.extractor_type: FailingHubExtractor() for hub in HUB_SOURCES}

    use_case = RunStartupDiscovery(
        uow_factory=make_uow_factory(repo),
        extractors=extractors,
        url_ingestion_submitter=submitter,
        max_per_run=10,
    )

    view = await use_case.execute()

    assert view.status == DiscoveryRunStatus.FAILED
    assert view.error_message is not None


@pytest.mark.anyio
async def test_get_discovery_run_returns_view_by_id():
    repo = FakeDiscoveryRunRepository()
    run = DiscoveryRun()
    run.start()
    run.complete(hubs_processed=1, urls_found=3, jobs_submitted=3)
    await repo.save(run)

    use_case = GetDiscoveryRun(make_uow_factory(repo))
    view = await use_case.execute(run.id)

    assert view.id == run.id
    assert view.status == DiscoveryRunStatus.COMPLETED


@pytest.mark.anyio
async def test_get_discovery_run_raises_not_found():
    repo = FakeDiscoveryRunRepository()
    use_case = GetDiscoveryRun(make_uow_factory(repo))

    with pytest.raises(DiscoveryRunNotFoundError):
        await use_case.execute(uuid4())


def test_discovery_run_entity_status_transitions():
    run = DiscoveryRun()
    assert run.status == DiscoveryRunStatus.PENDING

    run.start()
    assert run.status == DiscoveryRunStatus.RUNNING

    run.complete(hubs_processed=2, urls_found=10, jobs_submitted=10)
    assert run.status == DiscoveryRunStatus.COMPLETED
    assert run.hubs_processed == 2
    assert run.urls_found == 10


def test_discovery_run_entity_fail_transition():
    run = DiscoveryRun()
    run.start()
    run.fail("tudo quebrou")
    assert run.status == DiscoveryRunStatus.FAILED
    assert run.error_message == "tudo quebrou"
