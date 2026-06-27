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
from apps.api.src.modules.startups.domain.entities import Startup, StartupAIProfile, StartupEvidence
from apps.api.src.modules.startups.domain.enums import (
    AiDeploymentStage,
    AiGpuNeed,
    AiWorkloadType,
    FundingStage,
)
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
async def test_extract_startup_profile_persists_sector_and_description() -> None:
    uow = _make_uow()
    startup = Startup(name="Dadosfera")
    await uow.startup_repository.save(startup)

    outcome = ExtractionOutcome(
        sector="Data Analytics",
        description="Data platform with an AI agent that answers questions in natural language.",
    )
    extractor = FakeExtractionPort(outcome)

    use_case = ExtractStartupProfile(lambda: uow, extractor)
    view = await use_case.execute(
        ExtractStartupProfileInput(startup_id=startup.id)
    )

    assert view.sector == "Data Analytics"
    assert view.description == (
        "Data platform with an AI agent that answers questions in natural language."
    )


@pytest.mark.anyio
async def test_extract_startup_profile_does_not_erase_sector_when_outcome_has_none() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI", sector="LLM customer service", description="Existing description")
    await uow.startup_repository.save(startup)

    outcome = ExtractionOutcome(founders=["Ana Silva"])
    extractor = FakeExtractionPort(outcome)

    use_case = ExtractStartupProfile(lambda: uow, extractor)
    view = await use_case.execute(
        ExtractStartupProfileInput(startup_id=startup.id)
    )

    assert view.sector == "LLM customer service"
    assert view.description == "Existing description"


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
async def test_extract_startup_profile_persists_ai_profile() -> None:
    """Quando o outcome tem ai_profile, ele e salvo na startup."""

    uow = _make_uow()
    startup = Startup(name="VoiceBot AI")
    await uow.startup_repository.save(startup)

    profile = StartupAIProfile(
        ai_workload_type=AiWorkloadType.SPEECH,
        deployment_stage=AiDeploymentStage.PRODUCTION,
        gpu_need=AiGpuNeed.HIGH,
        current_tools=("PyTorch", "Kubernetes"),
        business_goal="Reduzir custo de atendimento via voz.",
        field_confidence={"ai_workload_type": 0.95, "gpu_need": 0.8},
    )
    outcome = ExtractionOutcome(ai_profile=profile)
    extractor = FakeExtractionPort(outcome)

    use_case = ExtractStartupProfile(lambda: uow, extractor)
    await use_case.execute(ExtractStartupProfileInput(startup_id=startup.id))

    saved = uow.startup_repository.items[startup.id]
    assert saved.ai_profile is not None
    assert saved.ai_profile.ai_workload_type is AiWorkloadType.SPEECH
    assert saved.ai_profile.deployment_stage is AiDeploymentStage.PRODUCTION
    assert saved.ai_profile.gpu_need is AiGpuNeed.HIGH
    assert "PyTorch" in saved.ai_profile.current_tools
    assert saved.ai_profile.field_confidence["ai_workload_type"] == 0.95


@pytest.mark.anyio
async def test_extract_startup_profile_no_ai_profile_leaves_existing_intact() -> None:
    """Quando o outcome nao tem ai_profile, o campo existente nao e apagado."""

    uow = _make_uow()
    startup = Startup(name="Acme AI")
    existing_profile = StartupAIProfile(ai_workload_type=AiWorkloadType.NLP)
    startup.update_ai_profile(existing_profile)
    await uow.startup_repository.save(startup)

    outcome = ExtractionOutcome(founders=["Ana Silva"])
    extractor = FakeExtractionPort(outcome)

    use_case = ExtractStartupProfile(lambda: uow, extractor)
    await use_case.execute(ExtractStartupProfileInput(startup_id=startup.id))

    saved = uow.startup_repository.items[startup.id]
    assert saved.ai_profile is not None
    assert saved.ai_profile.ai_workload_type is AiWorkloadType.NLP


@pytest.mark.anyio
async def test_try_extract_is_noop_when_extractor_unavailable() -> None:
    uow = _make_uow()
    startup = Startup(name="Acme AI")
    await uow.startup_repository.save(startup)

    use_case = ExtractStartupProfile(lambda: uow, None)

    await use_case.try_extract(startup.id)

    assert uow.startup_repository.items[startup.id].founders == ()
