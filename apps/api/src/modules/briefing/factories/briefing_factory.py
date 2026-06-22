"""Composicao das dependencias concretas do modulo briefing."""

from apps.api.src.modules.briefing.application.use_cases.generate_briefing import (
    GenerateBriefing,
)
from apps.api.src.modules.briefing.application.use_cases.get_briefing import (
    GetBriefing,
)
from apps.api.src.modules.briefing.application.use_cases.list_briefings import (
    ListBriefings,
)
from apps.api.src.modules.briefing.application.public.briefing_generator import (
    BriefingGenerator,
)
from apps.api.src.modules.briefing.infrastructure.database.postgres_unit_of_work import (
    PostgresBriefingsUnitOfWork,
)
from apps.api.src.modules.briefing.infrastructure.recommendations_adapters.recommendations_adapter import (
    RecommendationsModuleSource,
)
from apps.api.src.modules.briefing.infrastructure.startups_adapters.startup_profile_adapter import (
    StartupsModuleProfileSource,
)
from apps.api.src.modules.recommendations.factories.recommendations_factory import (
    RecommendationsFactory,
)
from apps.api.src.modules.startups.factories.startups_factory import StartupsFactory


class BriefingFactory:
    """Ponto de composicao do modulo briefing."""

    @staticmethod
    def create_generate_briefing() -> GenerateBriefing:
        profile_source = StartupsModuleProfileSource(
            StartupsFactory.create_startup_profile_reader()
        )
        recommendations_source = RecommendationsModuleSource(
            RecommendationsFactory.create_recommendations_reader()
        )
        return GenerateBriefing(
            PostgresBriefingsUnitOfWork,
            profile_source,
            recommendations_source,
        )

    @staticmethod
    def create_get_briefing() -> GetBriefing:
        return GetBriefing(PostgresBriefingsUnitOfWork)

    @staticmethod
    def create_list_briefings() -> ListBriefings:
        return ListBriefings(PostgresBriefingsUnitOfWork)

    @staticmethod
    def create_briefing_generator() -> BriefingGenerator:
        profile_source = StartupsModuleProfileSource(
            StartupsFactory.create_startup_profile_reader()
        )
        recommendations_source = RecommendationsModuleSource(
            RecommendationsFactory.create_recommendations_reader()
        )
        return GenerateBriefing(
            PostgresBriefingsUnitOfWork,
            profile_source,
            recommendations_source,
        )
