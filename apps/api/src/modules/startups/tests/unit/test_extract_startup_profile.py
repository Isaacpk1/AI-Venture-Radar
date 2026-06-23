"""Testes do caso de uso ExtractStartupProfile."""

from uuid import uuid4

import pytest

from apps.api.src.modules.startups.application.dto import ExtractStartupProfileInput
from apps.api.src.modules.startups.application.ports import (
    ExtractionOutcome,
    ExtractionPort,
)
from apps.api.src.modules.startups.application.use_cases.extract_startup_profile import (
    ExtractStartupProfile,
)
from apps.api.src.modules.startups.domain.entities import Startup, StartupEvidence
from apps.api.src.modules.startups.domain.enums import FundingStage
from apps.api.src.modules.startups.domain.exceptions import (
    StartupExtractionUnavailableError,
    StartupNotFoundError,
)
from apps.api.src.modules.startups.tests.unit.test_startup_use_cases import (
    FakeEvidenceRepository,
    FakeStartupRepository,
    FakeUoW,
)


def _make_uow() -> FakeUoW:
    return FakeUoW(FakeStartupRepository(), FakeEvidenceRepository())


class FakeExtractionPort(ExtractionPort):
    def __init__(self, outcome: ExtractionOutcome) -> None:
        self.outcome = outcome
        self.received_evidence_texts: list[str] | None = None

    async def extract(
        self,
        *,
        name: str,
        sector: str | None,
        description: str | None,
        evidence_texts: list[str],
    ) -> ExtractionOutcome:
        self.received_evidence_texts = evidence_texts
        return self.outcome


@pytest.mark.anyio
async def test_extract_startup_profile_persists_outcome() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI", sector="LLM customer service")
    await uow.startup_repository.save(startup)
    evidence = StartupEvidence(
        startup_id=startup.id,
        scraping_result_id=uuid4(),
        source_url="https://example.com/news",
        title="Acme launches LLM chatbot",
        notes="Fundada por Ana Silva, Series A de USD 2M, cliente Empresa X.",
    )
    await uow.evidence_repository.save(evidence)

    outcome = ExtractionOutcome(
        founders=["Ana Silva"],
        funding_stage=FundingStage.SERIES_A,
        funding_amount_usd=2_000_000.0,
        customers=["Empresa X"],
    )
    extractor = FakeExtractionPort(outcome)

    use_case = ExtractStartupProfile(lambda: uow, extractor)
    view = await use_case.execute(
        ExtractStartupProfileInput(startup_id=startup.id)
    )

    assert view.founders == ["Ana Silva"]
    assert view.funding_stage is FundingStage.SERIES_A
    assert view.funding_amount_usd == 2_000_000.0
    assert view.customers == ["Empresa X"]
    assert extractor.received_evidence_texts == [
        "Acme launches LLM chatbot Fundada por Ana Silva, Series A de "
        "USD 2M, cliente Empresa X."
    ]


@pytest.mark.anyio
async def test_extract_startup_profile_raises_when_startup_missing() -> None:
    uow = _make_uow()
    extractor = FakeExtractionPort(ExtractionOutcome())

    use_case = ExtractStartupProfile(lambda: uow, extractor)

    with pytest.raises(StartupNotFoundError):
        await use_case.execute(ExtractStartupProfileInput(startup_id=uuid4()))


@pytest.mark.anyio
async def test_extract_startup_profile_raises_when_extractor_unavailable() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI")
    await uow.startup_repository.save(startup)

    use_case = ExtractStartupProfile(lambda: uow, None)

    with pytest.raises(StartupExtractionUnavailableError):
        await use_case.execute(
            ExtractStartupProfileInput(startup_id=startup.id)
        )


@pytest.mark.anyio
async def test_try_extract_persists_outcome() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI")
    await uow.startup_repository.save(startup)
    outcome = ExtractionOutcome(founders=["Ana Silva"])
    extractor = FakeExtractionPort(outcome)

    use_case = ExtractStartupProfile(lambda: uow, extractor)
    await use_case.try_extract(startup.id)

    assert uow.startup_repository.items[startup.id].founders == ("Ana Silva",)


@pytest.mark.anyio
async def test_try_extract_is_noop_when_extractor_unavailable() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI")
    await uow.startup_repository.save(startup)

    use_case = ExtractStartupProfile(lambda: uow, None)

    await use_case.try_extract(startup.id)

    assert uow.startup_repository.items[startup.id].founders == ()
