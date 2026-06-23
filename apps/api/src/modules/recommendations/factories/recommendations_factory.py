"""Composicao das dependencias concretas do modulo recommendations."""

from apps.api.src.modules.nvidia_knowledge.factories.nvidia_knowledge_factory import (
    NvidiaKnowledgeFactory,
)
from apps.api.src.modules.recommendations.application.use_cases.generate_recommendations import (
    GenerateRecommendations,
)
from apps.api.src.modules.recommendations.application.use_cases.get_recommendation import (
    GetRecommendation,
)
from apps.api.src.modules.recommendations.application.use_cases.list_recommendations import (
    ListRecommendations,
)
from apps.api.src.modules.recommendations.application.public.recommendation_generator import (
    RecommendationGenerator,
)
from apps.api.src.modules.recommendations.application.public.recommendation_justification_updater import (
    RecommendationJustificationUpdater,
)
from apps.api.src.modules.recommendations.application.public.recommendations_reader import (
    RecommendationsReader,
)
from apps.api.src.modules.recommendations.application.use_cases.update_recommendation_justifications import (
    UpdateRecommendationJustifications,
)
from apps.api.src.modules.recommendations.infrastructure.database.postgres_unit_of_work import (
    PostgresRecommendationsUnitOfWork,
)
from apps.api.src.modules.recommendations.infrastructure.nvidia_adapters.nvidia_catalog_adapter import (
    NvidiaKnowledgeCatalogAdapter,
)
from apps.api.src.modules.recommendations.infrastructure.startups_adapters.startup_profile_adapter import (
    StartupsModuleProfileSource,
)
from apps.api.src.modules.startups.factories.startups_factory import StartupsFactory


class RecommendationsFactory:
    """Ponto de composicao do modulo recommendations."""

    @staticmethod
    def create_generate_recommendations() -> GenerateRecommendations:
        catalog_source = NvidiaKnowledgeCatalogAdapter(
            NvidiaKnowledgeFactory.create_catalog()
        )
        profile_source = StartupsModuleProfileSource(
            StartupsFactory.create_startup_profile_reader()
        )
        return GenerateRecommendations(
            PostgresRecommendationsUnitOfWork,
            profile_source,
            catalog_source,
        )

    @staticmethod
    def create_recommendation_justification_updater() -> RecommendationJustificationUpdater:
        return UpdateRecommendationJustifications(PostgresRecommendationsUnitOfWork)

    @staticmethod
    def create_get_recommendation() -> GetRecommendation:
        return GetRecommendation(PostgresRecommendationsUnitOfWork)

    @staticmethod
    def create_list_recommendations() -> ListRecommendations:
        return ListRecommendations(PostgresRecommendationsUnitOfWork)

    @staticmethod
    def create_recommendations_reader() -> RecommendationsReader:
        return ListRecommendations(PostgresRecommendationsUnitOfWork)

    @staticmethod
    def create_recommendation_generator() -> RecommendationGenerator:
        catalog_source = NvidiaKnowledgeCatalogAdapter(
            NvidiaKnowledgeFactory.create_catalog()
        )
        profile_source = StartupsModuleProfileSource(
            StartupsFactory.create_startup_profile_reader()
        )
        return GenerateRecommendations(
            PostgresRecommendationsUnitOfWork,
            profile_source,
            catalog_source,
        )
