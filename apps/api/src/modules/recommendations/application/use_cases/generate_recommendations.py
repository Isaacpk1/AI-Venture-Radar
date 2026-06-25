"""Caso de uso para gerar recomendacoes NVIDIA para uma startup."""

import asyncio
from uuid import UUID

from apps.api.src.modules.recommendations.application.dto import (
    GenerateRecommendationsInput,
    GroundedJustification,
    RecommendationView,
)
from apps.api.src.modules.recommendations.application.ports import (
    NvidiaCatalogSource,
    NvidiaKnowledgeGrounder,
    StartupProfileSource,
)
from apps.api.src.modules.recommendations.application.public.recommendation_generator import (
    RecommendationGenerator,
)
from apps.api.src.modules.recommendations.application.unit_of_work import (
    RecommendationsUnitOfWorkFactory,
)
from apps.api.src.modules.recommendations.domain.entities import Recommendation
from apps.api.src.modules.recommendations.domain.policies import (
    EvidenceSignal,
    MatchResult,
    TechnologyCandidate,
    match_technologies,
)


class GenerateRecommendations(RecommendationGenerator):
    """Cruza o perfil da startup com o catalogo NVIDIA e persiste o resultado.

    Cada chamada substitui as recomendacoes anteriores da mesma startup -
    V1 nao versiona geracoes, apenas mantem o resultado mais recente.
    """

    def __init__(
        self,
        uow_factory: RecommendationsUnitOfWorkFactory,
        profile_source: StartupProfileSource,
        catalog_source: NvidiaCatalogSource,
        grounder: NvidiaKnowledgeGrounder | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._profile_source = profile_source
        self._catalog_source = catalog_source
        self._grounder = grounder

    async def generate(self, startup_id: UUID) -> list[RecommendationView]:
        profile = await self._profile_source.get_profile(startup_id)
        technologies = await self._catalog_source.list_technologies()

        evidence_signals = [
            EvidenceSignal(
                evidence_id=evidence.evidence_id,
                text=f"{evidence.title or ''} {evidence.notes or ''}".lower(),
            )
            for evidence in profile.evidences
        ]
        candidates = [
            TechnologyCandidate(
                slug=technology.slug,
                name=technology.name,
                category=technology.category,
                use_cases=technology.use_cases,
                keywords=technology.keywords,
            )
            for technology in technologies
        ]

        matches = match_technologies(
            sector=profile.sector,
            description=profile.description,
            ai_maturity_level=profile.ai_maturity_level,
            evidence_signals=evidence_signals,
            technologies=candidates,
        )

        grounded_results = await self._ground_matches(matches)
        recommendations = [
            self._to_recommendation(startup_id, match, grounded)
            for match, grounded in zip(matches, grounded_results, strict=True)
        ]

        async with self._uow_factory() as uow:
            await uow.recommendation_repository.delete_by_startup_id(startup_id)
            for recommendation in recommendations:
                await uow.recommendation_repository.save(recommendation)
            await uow.commit()

        return [to_recommendation_view(recommendation) for recommendation in recommendations]

    async def execute(
        self, recommendation_input: GenerateRecommendationsInput
    ) -> list[RecommendationView]:
        return await self.generate(recommendation_input.startup_id)

    async def _ground_matches(
        self, matches: list[MatchResult]
    ) -> list[GroundedJustification | None]:
        """Busca fundamentacao real em paralelo, 1 chamada RAG por match.

        Best-effort: sem grounder configurado, devolve `None` pra cada match
        sem nenhuma chamada de rede.
        """

        if self._grounder is None or not matches:
            return [None] * len(matches)

        return await asyncio.gather(
            *(
                self._grounder.ground(match.technology.name, _use_case(match))
                for match in matches
            )
        )

    @staticmethod
    def _to_recommendation(
        startup_id: UUID,
        match: MatchResult,
        grounded: GroundedJustification | None,
    ) -> Recommendation:
        return Recommendation(
            startup_id=startup_id,
            technology_slug=match.technology.slug,
            technology_name=match.technology.name,
            category=match.technology.category,
            score=match.score,
            justification=(
                _build_grounded_justification(grounded)
                if grounded is not None
                else _build_justification(match)
            ),
            matched_keywords=match.matched_keywords,
            evidence_ids=match.evidence_ids,
        )


def _use_case(match: MatchResult) -> str:
    return match.technology.use_cases[0] if match.technology.use_cases else (
        match.technology.name
    )


def _build_justification(match: MatchResult) -> str:
    keywords = ", ".join(match.matched_keywords)
    return (
        f"Evidencias e perfil mencionam: {keywords}. "
        f"{match.technology.name} e indicada para: {_use_case(match)}."
    )


def _build_grounded_justification(grounded: GroundedJustification) -> str:
    """Citacoes como link Markdown (`[Fonte N](url)`), nao URL puro.

    Necessario pra rastreabilidade ponta a ponta (P3): o frontend renderiza
    `justification` como Markdown de verdade desde o fechamento dessa
    decisao - URL puro nao virava link clicavel sem essa sintaxe.
    """

    sources = ", ".join(
        f"[Fonte {index}]({url})"
        for index, url in enumerate(grounded.citation_urls, start=1)
    )
    return f"{grounded.text} Fontes: {sources}."


def to_recommendation_view(recommendation: Recommendation) -> RecommendationView:
    return RecommendationView(
        id=recommendation.id,
        startup_id=recommendation.startup_id,
        technology_slug=recommendation.technology_slug,
        technology_name=recommendation.technology_name,
        category=recommendation.category,
        score=recommendation.score,
        justification=recommendation.justification,
        matched_keywords=list(recommendation.matched_keywords),
        evidence_ids=list(recommendation.evidence_ids),
        created_at=recommendation.created_at,
    )
