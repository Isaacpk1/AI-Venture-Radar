"""Composicao das dependencias concretas do modulo orchestration."""

from apps.api.src.modules.briefing.factories.briefing_factory import BriefingFactory
from apps.api.src.modules.embeddings.factories.embeddings_factory import EmbeddingsFactory
from apps.api.src.modules.ingestion.factories.ingestion_factory import IngestionFactory
from apps.api.src.modules.orchestration.application.use_cases.advance_url_ingestion_job import (
    AdvanceUrlIngestionJob,
)
from apps.api.src.modules.orchestration.application.use_cases.create_url_ingestion_job import (
    CreateUrlIngestionJob,
)
from apps.api.src.modules.orchestration.application.use_cases.execute_analysis_job import (
    ExecuteAnalysisJob,
)
from apps.api.src.modules.orchestration.application.use_cases.get_analysis_job import (
    GetAnalysisJob,
)
from apps.api.src.modules.orchestration.application.use_cases.get_url_ingestion_job import (
    GetUrlIngestionJob,
)
from apps.api.src.modules.orchestration.infrastructure.embeddings_adapters.embeddings_adapter import (
    EmbeddingsModulePort,
)
from apps.api.src.modules.orchestration.infrastructure.ingestion_adapters.ingestion_adapter import (
    IngestionModulePort,
)
from apps.api.src.modules.orchestration.infrastructure.queue.dramatiq_url_ingestion_dispatcher import (
    DramatiqUrlIngestionJobPublisher,
    DramatiqUrlIngestionTaskDispatcher,
)
from apps.api.src.modules.orchestration.infrastructure.scraping_adapters.scraping_adapter import (
    ScrapingModulePort,
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
from apps.api.src.modules.scraping.factories.scraping_factory import ScrapingFactory
from apps.api.src.shared.queue.dramatiq_broker import broker


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

    @staticmethod
    def create_url_ingestion_task_dispatcher() -> DramatiqUrlIngestionTaskDispatcher:
        return DramatiqUrlIngestionTaskDispatcher(
            DramatiqUrlIngestionJobPublisher(broker)
        )

    @staticmethod
    def create_create_url_ingestion_job() -> CreateUrlIngestionJob:
        return CreateUrlIngestionJob(
            PostgresAnalysisUnitOfWork,
            OrchestrationFactory.create_url_ingestion_task_dispatcher(),
        )

    @staticmethod
    def create_get_url_ingestion_job() -> GetUrlIngestionJob:
        return GetUrlIngestionJob(PostgresAnalysisUnitOfWork)

    @staticmethod
    def create_advance_url_ingestion_job() -> AdvanceUrlIngestionJob:
        return AdvanceUrlIngestionJob(
            uow_factory=PostgresAnalysisUnitOfWork,
            scraping_port=ScrapingModulePort(ScrapingFactory.create_job_submitter()),
            ingestion_port=IngestionModulePort(IngestionFactory.create_job_submitter()),
            embeddings_port=EmbeddingsModulePort(
                EmbeddingsFactory.create_job_submitter()
            ),
        )
