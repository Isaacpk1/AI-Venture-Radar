"""Testes do caso de uso GenerateRecommendations."""

from types import TracebackType
from uuid import UUID, uuid4

import pytest

from apps.api.src.modules.recommendations.application.dto import (
    EvidenceSnapshot,
    GenerateRecommendationsInput,
    NvidiaTechnologySnapshot,
    StartupProfileSnapshot,
)
from apps.api.src.modules.recommendations.application.ports import (
    NvidiaCatalogSource,
    StartupProfileSource,
)
from apps.api.src.modules.recommendations.application.unit_of_work import (
    RecommendationsUnitOfWork,
)
from apps.api.src.modules.recommendations.application.use_cases.generate_recommendations import (
    GenerateRecommendations,
)
from apps.api.src.modules.recommendations.domain.entities import Recommendation
from apps.api.src.modules.recommendations.domain.exceptions import (
    StartupProfileUnavailableError,
)
from apps.api.src.modules.recommendations.domain.repositories import (
    RecommendationRepository,
)

NIM_SNAPSHOT = NvidiaTechnologySnapshot(
    slug="nvidia-nim",
    name="NVIDIA NIM",
    category="model_serving",
    use_cases=("servir LLMs em producao",),
    keywords=("llm", "generative ai", "inference", "api", "deployment", "microservice"),
)


class FakeProfileSource(StartupProfileSource):
    def __init__(self, profile: StartupProfileSnapshot | None) -> None:
        self._profile = profile

    async def get_profile(self, startup_id: UUID) -> StartupProfileSnapshot:
        if self._profile is None:
            raise StartupProfileUnavailableError(f"Startup {startup_id} nao encontrada.")
        return self._profile


class FakeCatalogSource(NvidiaCatalogSource):
    def __init__(self, technologies: list[NvidiaTechnologySnapshot]) -> None:
        self._technologies = technologies

    async def list_technologies(self) -> list[NvidiaTechnologySnapshot]:
        return self._technologies


class FakeRecommendationRepository(RecommendationRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Recommendation] = {}
        self.deleted_for_startup: list[UUID] = []

    async def save(self, recommendation: Recommendation) -> None:
        self.items[recommendation.id] = recommendation

    async def delete_by_startup_id(self, startup_id: UUID) -> None:
        self.deleted_for_startup.append(startup_id)
        self.items = {
            rec_id: rec
            for rec_id, rec in self.items.items()
            if rec.startup_id != startup_id
        }

    async def get_by_id(self, recommendation_id: UUID) -> Recommendation | None:
        return self.items.get(recommendation_id)

    async def list_by_startup_id(self, startup_id: UUID) -> list[Recommendation]:
        return [rec for rec in self.items.values() if rec.startup_id == startup_id]


class FakeUoW(RecommendationsUnitOfWork):
    def __init__(self, repository: FakeRecommendationRepository) -> None:
        self.recommendation_repository = repository
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


@pytest.mark.anyio
async def test_generate_recommendations_persists_matches() -> None:
    startup_id = uuid4()
    repository = FakeRecommendationRepository()
    uow = FakeUoW(repository)
    profile_source = FakeProfileSource(
        StartupProfileSnapshot(
            sector="LLM and generative AI",
            description="Provides inference API with simple deployment as microservice.",
            evidences=(),
        )
    )
    catalog_source = FakeCatalogSource([NIM_SNAPSHOT])

    use_case = GenerateRecommendations(lambda: uow, profile_source, catalog_source)
    views = await use_case.execute(GenerateRecommendationsInput(startup_id=startup_id))

    assert len(views) == 1
    assert views[0].technology_slug == "nvidia-nim"
    assert views[0].startup_id == startup_id
    assert uow.commits == 1
    assert len(repository.items) == 1


@pytest.mark.anyio
async def test_generate_recommendations_replaces_previous_batch() -> None:
    startup_id = uuid4()
    repository = FakeRecommendationRepository()
    await repository.save(
        Recommendation(
            startup_id=startup_id,
            technology_slug="old-tech",
            technology_name="Old Tech",
            category="legacy",
            score=0.5,
            justification="recomendacao antiga",
        )
    )
    uow = FakeUoW(repository)
    profile_source = FakeProfileSource(
        StartupProfileSnapshot(sector="LLM and generative AI", description=None, evidences=())
    )
    catalog_source = FakeCatalogSource([NIM_SNAPSHOT])

    use_case = GenerateRecommendations(lambda: uow, profile_source, catalog_source)
    await use_case.execute(GenerateRecommendationsInput(startup_id=startup_id))

    remaining_slugs = [rec.technology_slug for rec in repository.items.values()]
    assert "old-tech" not in remaining_slugs
    assert startup_id in repository.deleted_for_startup


@pytest.mark.anyio
async def test_generate_recommendations_propagates_unavailable_profile() -> None:
    repository = FakeRecommendationRepository()
    uow = FakeUoW(repository)
    profile_source = FakeProfileSource(None)
    catalog_source = FakeCatalogSource([NIM_SNAPSHOT])

    use_case = GenerateRecommendations(lambda: uow, profile_source, catalog_source)

    with pytest.raises(StartupProfileUnavailableError):
        await use_case.execute(GenerateRecommendationsInput(startup_id=uuid4()))


@pytest.mark.anyio
async def test_generate_recommendations_tracks_evidence_ids() -> None:
    startup_id = uuid4()
    evidence_id = uuid4()
    repository = FakeRecommendationRepository()
    uow = FakeUoW(repository)
    profile_source = FakeProfileSource(
        StartupProfileSnapshot(
            sector=None,
            description=None,
            evidences=(
                EvidenceSnapshot(
                    evidence_id=evidence_id,
                    title="Our new generative AI inference API deployment",
                    notes="microservice rollout",
                ),
            ),
        )
    )
    catalog_source = FakeCatalogSource([NIM_SNAPSHOT])

    use_case = GenerateRecommendations(lambda: uow, profile_source, catalog_source)
    views = await use_case.execute(GenerateRecommendationsInput(startup_id=startup_id))

    assert len(views) == 1
    assert views[0].evidence_ids == [evidence_id]
