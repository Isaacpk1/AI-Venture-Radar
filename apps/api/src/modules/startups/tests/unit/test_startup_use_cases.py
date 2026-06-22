"""Testes dos casos de uso do modulo startups."""

from types import TracebackType
from uuid import UUID, uuid4

import pytest

from apps.api.src.modules.startups.application.dto import (
    AddStartupEvidenceInput,
    CreateStartupInput,
    UpdateStartupInput,
)
from apps.api.src.modules.startups.application.unit_of_work import StartupsUnitOfWork
from apps.api.src.modules.startups.application.use_cases.add_startup_evidence import (
    AddStartupEvidence,
)
from apps.api.src.modules.startups.application.use_cases.create_startup import (
    CreateStartup,
)
from apps.api.src.modules.startups.application.use_cases.get_startup import GetStartup
from apps.api.src.modules.startups.application.use_cases.list_startup_evidences import (
    ListStartupEvidences,
)
from apps.api.src.modules.startups.application.use_cases.update_startup import (
    UpdateStartup,
)
from apps.api.src.modules.startups.domain.entities import Startup, StartupEvidence
from apps.api.src.modules.startups.domain.enums import FundingStage, StartupEvidenceType
from apps.api.src.modules.startups.domain.exceptions import StartupNotFoundError
from apps.api.src.modules.startups.domain.repositories import (
    StartupEvidenceRepository,
    StartupRepository,
)


class FakeStartupRepository(StartupRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Startup] = {}

    async def save(self, startup: Startup) -> None:
        self.items[startup.id] = startup

    async def get_by_id(self, startup_id: UUID) -> Startup | None:
        return self.items.get(startup_id)


class FakeEvidenceRepository(StartupEvidenceRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, StartupEvidence] = {}

    async def save(self, evidence: StartupEvidence) -> None:
        self.items[evidence.id] = evidence

    async def get_by_id(self, evidence_id: UUID) -> StartupEvidence | None:
        return self.items.get(evidence_id)

    async def list_by_startup_id(self, startup_id: UUID) -> list[StartupEvidence]:
        return [
            evidence
            for evidence in self.items.values()
            if evidence.startup_id == startup_id
        ]


class FakeUoW(StartupsUnitOfWork):
    def __init__(
        self,
        startup_repository: FakeStartupRepository,
        evidence_repository: FakeEvidenceRepository,
    ) -> None:
        self.startup_repository = startup_repository
        self.evidence_repository = evidence_repository
        self.commits = 0

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
        self.commits += 1

    async def rollback(self) -> None:
        pass


def _make_uow() -> FakeUoW:
    return FakeUoW(FakeStartupRepository(), FakeEvidenceRepository())


@pytest.mark.anyio
async def test_create_startup_persists_and_returns_view() -> None:
    uow = _make_uow()
    use_case = CreateStartup(lambda: uow)

    view = await use_case.execute(
        CreateStartupInput(
            name="Acme AI",
            website_url="https://acme.example.com",
            sector="AI Infra",
        )
    )

    assert view.name == "Acme AI"
    assert view.id in uow.startup_repository.items
    assert uow.commits == 1


@pytest.mark.anyio
async def test_get_startup_returns_existing_startup() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI")
    await uow.startup_repository.save(startup)

    view = await GetStartup(lambda: uow).execute(startup_id=startup.id)

    assert view.id == startup.id


@pytest.mark.anyio
async def test_get_startup_raises_when_missing() -> None:
    uow = _make_uow()

    with pytest.raises(StartupNotFoundError):
        await GetStartup(lambda: uow).execute(startup_id=uuid4())


@pytest.mark.anyio
async def test_update_startup_changes_existing_record() -> None:
    uow = _make_uow()
    startup = Startup(name="Old")
    await uow.startup_repository.save(startup)

    view = await UpdateStartup(lambda: uow).execute(
        UpdateStartupInput(startup_id=startup.id, name="New", country="BR")
    )

    assert view.name == "New"
    assert view.country == "BR"
    assert uow.startup_repository.items[startup.id].name == "New"


@pytest.mark.anyio
async def test_update_startup_sets_structured_fields() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI")
    await uow.startup_repository.save(startup)

    view = await UpdateStartup(lambda: uow).execute(
        UpdateStartupInput(
            startup_id=startup.id,
            founders=["Ana Silva"],
            funding_stage=FundingStage.SERIES_A,
            funding_amount_usd=2_000_000.0,
            customers=["Empresa X"],
        )
    )

    assert view.founders == ["Ana Silva"]
    assert view.funding_stage is FundingStage.SERIES_A
    assert view.funding_amount_usd == 2_000_000.0
    assert view.customers == ["Empresa X"]


@pytest.mark.anyio
async def test_add_evidence_requires_existing_startup() -> None:
    uow = _make_uow()

    with pytest.raises(StartupNotFoundError):
        await AddStartupEvidence(lambda: uow).execute(
            AddStartupEvidenceInput(
                startup_id=uuid4(),
                scraping_result_id=uuid4(),
                source_url="https://example.com",
            )
        )


@pytest.mark.anyio
async def test_add_and_list_startup_evidences() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI")
    await uow.startup_repository.save(startup)

    evidence_view = await AddStartupEvidence(lambda: uow).execute(
        AddStartupEvidenceInput(
            startup_id=startup.id,
            scraping_result_id=uuid4(),
            source_url="https://example.com/news",
            evidence_type=StartupEvidenceType.NEWS,
            confidence_score=0.9,
        )
    )
    evidences = await ListStartupEvidences(lambda: uow).execute(
        startup_id=startup.id
    )

    assert evidence_view.evidence_type is StartupEvidenceType.NEWS
    assert len(evidences) == 1
    assert evidences[0].id == evidence_view.id
