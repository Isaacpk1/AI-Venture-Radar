"""Caso de uso para gerar o briefing executivo de uma startup."""

from uuid import UUID

from apps.api.src.modules.briefing.application.dto import (
    BriefingView,
    GenerateBriefingInput,
)
from apps.api.src.modules.briefing.application.ports import (
    RecommendationsSource,
    StartupProfileSource,
)
from apps.api.src.modules.briefing.application.public.briefing_generator import (
    BriefingGenerator,
)
from apps.api.src.modules.briefing.application.unit_of_work import (
    BriefingsUnitOfWorkFactory,
)
from apps.api.src.modules.briefing.domain.entities import Briefing
from apps.api.src.modules.briefing.domain.policies import (
    EvidenceItem,
    RecommendationItem,
    StartupSummary,
    assess_risks,
    build_briefing_markdown,
    suggest_next_actions,
)


class GenerateBriefing(BriefingGenerator):
    """Monta e persiste o briefing executivo mais recente de uma startup.

    Cada chamada substitui o briefing anterior da mesma startup - V1 nao
    versiona geracoes, apenas mantem o resultado mais recente (mesma decisao
    de ``GenerateRecommendations``).
    """

    def __init__(
        self,
        uow_factory: BriefingsUnitOfWorkFactory,
        profile_source: StartupProfileSource,
        recommendations_source: RecommendationsSource,
    ) -> None:
        self._uow_factory = uow_factory
        self._profile_source = profile_source
        self._recommendations_source = recommendations_source

    async def generate(self, startup_id: UUID) -> BriefingView:
        profile = await self._profile_source.get_profile(startup_id)
        recommendation_snapshots = await self._recommendations_source.list_by_startup(
            startup_id
        )

        startup = StartupSummary(
            name=profile.startup.name,
            sector=profile.startup.sector,
            description=profile.startup.description,
            country=profile.startup.country,
            website_url=profile.startup.website_url,
        )
        evidences = [
            EvidenceItem(
                title=evidence.title,
                source_url=evidence.source_url,
                evidence_type=evidence.evidence_type,
                confidence_score=evidence.confidence_score,
            )
            for evidence in profile.evidences
        ]
        recommendations = [
            RecommendationItem(
                technology_name=recommendation.technology_name,
                category=recommendation.category,
                score=recommendation.score,
                justification=recommendation.justification,
            )
            for recommendation in recommendation_snapshots
        ]

        risks = assess_risks(evidences, recommendations)
        next_actions = suggest_next_actions(recommendations)
        content = build_briefing_markdown(
            startup=startup,
            evidences=evidences,
            recommendations=recommendations,
            risks=risks,
            next_actions=next_actions,
        )

        briefing = Briefing(startup_id=startup_id, content=content)

        async with self._uow_factory() as uow:
            await uow.briefing_repository.delete_by_startup_id(startup_id)
            await uow.briefing_repository.save(briefing)
            await uow.commit()

        return to_briefing_view(briefing)

    async def execute(self, briefing_input: GenerateBriefingInput) -> BriefingView:
        return await self.generate(briefing_input.startup_id)


def to_briefing_view(briefing: Briefing) -> BriefingView:
    return BriefingView(
        id=briefing.id,
        startup_id=briefing.startup_id,
        content=briefing.content,
        generated_at=briefing.generated_at,
    )
