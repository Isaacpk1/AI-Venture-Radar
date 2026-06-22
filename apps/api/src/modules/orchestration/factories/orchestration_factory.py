"""Composicao das dependencias concretas do modulo orchestration."""

from apps.api.src.modules.briefing.factories.briefing_factory import BriefingFactory
from apps.api.src.modules.orchestration.application.use_cases.execute_analysis_job import (
    ExecuteAnalysisJob,
)
from apps.api.src.modules.orchestration.application.use_cases.get_analysis_job import (
    GetAnalysisJob,
)
from apps.api.src.modules.orchestration.application.use_cases.list_analysis_jobs import (
    ListAnalysisJobs,
)
from apps.api.src.modules.orchestration.infrastructure.briefing_adapters.briefing_adapter import (
    BriefingModulePort,
)
from apps.api.src.modules.orchestration.infrastructure.database.postgres_unit_of_work import (
    PostgresAnalysisUnitOfWork,
)
from apps.api.src.modules.orchestration.infrastructure.recommendations_adapters.recommendations_adapter import (
    RecommendationsModulePort,
)
from apps.api.src.modules.recommendations.factories.recommendations_factory import (
    RecommendationsFactory,
)


class OrchestrationFactory:
    """Ponto de composicao do modulo orchestration."""

    @staticmethod
    def create_execute_analysis_job() -> ExecuteAnalysisJob:
        recommendations_port = RecommendationsModulePort(
            RecommendationsFactory.create_recommendation_generator()
        )
        briefing_port = BriefingModulePort(
            BriefingFactory.create_briefing_generator()
        )
        return ExecuteAnalysisJob(
            PostgresAnalysisUnitOfWork,
            recommendations_port,
            briefing_port,
        )

    @staticmethod
    def create_get_analysis_job() -> GetAnalysisJob:
        return GetAnalysisJob(PostgresAnalysisUnitOfWork)

    @staticmethod
    def create_list_analysis_jobs() -> ListAnalysisJobs:
        return ListAnalysisJobs(PostgresAnalysisUnitOfWork)
