"""Composicao das dependencias concretas do modulo de scraping."""

from apps.api.src.modules.scraping.application.quality_scoring_service import (
    QualityScoringService,
)
from apps.api.src.modules.scraping.application.scraping_limits import (
    PipelineLimits,
    ScrapingLimits,
)
from apps.api.src.modules.scraping.application.scraping_pipeline import (
    ScrapingPipeline,
)
from apps.api.src.modules.scraping.application.strategy_selector import (
    ScrapingStrategySelector,
)
from apps.api.src.modules.scraping.application.use_cases.create_scraping_job import (
    CreateScrapingJob,
)
from apps.api.src.modules.scraping.application.use_cases.execute_scraping_job import (
    ExecuteScrapingJob,
)
from apps.api.src.modules.scraping.application.use_cases.get_scraping_job import (
    GetScrapingJob,
)
from apps.api.src.modules.scraping.application.use_cases.get_scraping_result import (
    GetScrapingResult,
)
from apps.api.src.modules.scraping.domain.policies import (
    ContentAcceptancePolicy,
    FallbackPolicy,
    ValidationDecisionPolicy,
)
from apps.api.src.modules.scraping.domain.repositories import ScrapingAttemptRepository
from apps.api.src.modules.scraping.infrastructure.database.postgres_unit_of_work import (
    PostgresScrapingUnitOfWork,
)
from apps.api.src.modules.scraping.infrastructure.queue.dramatiq_broker import broker
from apps.api.src.modules.scraping.infrastructure.queue.dramatiq_task_dispatcher import (
    DramatiqJobPublisher,
    DramatiqTaskDispatcher,
)
from apps.api.src.modules.scraping.infrastructure.scrapers.beautifulsoup_scraper import (
    BeautifulSoupScraper,
)
from apps.api.src.modules.scraping.infrastructure.scrapers.playwright_scraper import (
    PlaywrightScraper,
)
from apps.api.src.modules.scraping.infrastructure.security.url_guard import UrlGuard
from apps.api.src.modules.scraping.infrastructure.validators.deterministic_validator import (
    BasicDeterministicValidator,
)


class ScrapingFactory:
    """Cria casos de uso com todas as dependencias concretas necessarias.

    Este e o ponto de composicao: ele conhece PostgreSQL, BeautifulSoup e o
    dispatcher Dramatiq, enquanto os casos de uso continuam dependendo apenas de
    contratos definidos pelas camadas internas.
    """

    @staticmethod
    def create_unit_of_work() -> PostgresScrapingUnitOfWork:
        """Cria uma nova sessao/transacao PostgreSQL para cada operacao."""

        return PostgresScrapingUnitOfWork()

    @staticmethod
    def create_pipeline(
        attempt_repository: ScrapingAttemptRepository,
    ) -> ScrapingPipeline:
        """Monta a pipeline usando o repositorio da transacao atual."""

        beautifulsoup_scraper = BeautifulSoupScraper(
            url_guard=UrlGuard(),
            limits=ScrapingLimits(),
        )
        playwright_scraper = PlaywrightScraper(
            url_guard=UrlGuard(),
            # Renderizar JavaScript normalmente exige mais tempo que baixar
            # HTML estatico, por isso esta estrategia recebe timeout maior.
            limits=ScrapingLimits(timeout_seconds=30),
        )

        return ScrapingPipeline(
            strategy_selector=ScrapingStrategySelector(
                [beautifulsoup_scraper, playwright_scraper]
            ),
            validator=BasicDeterministicValidator(),
            scoring_service=QualityScoringService(),
            decision_policy=ValidationDecisionPolicy(
                ContentAcceptancePolicy(),
                FallbackPolicy(),
            ),
            attempt_repository=attempt_repository,
            limits=PipelineLimits(),
        )

    @classmethod
    def create_execute_scraping_job(cls) -> ExecuteScrapingJob:
        """Cria o caso de uso executado pelo dispatcher ou futuro worker."""

        return ExecuteScrapingJob(
            unit_of_work_factory=cls.create_unit_of_work,
            pipeline_factory=cls.create_pipeline,
        )

    @classmethod
    def create_create_scraping_job(cls) -> CreateScrapingJob:
        """Cria o caso de uso que persiste e despacha novos jobs."""

        return CreateScrapingJob(
            unit_of_work_factory=cls.create_unit_of_work,
            task_dispatcher=DramatiqTaskDispatcher(
                DramatiqJobPublisher(broker),
            ),
        )

    @classmethod
    def create_get_scraping_job(cls) -> GetScrapingJob:
        """Cria o caso de uso de consulta de job e tentativas."""

        return GetScrapingJob(unit_of_work_factory=cls.create_unit_of_work)

    @classmethod
    def create_get_scraping_result(cls) -> GetScrapingResult:
        """Cria o caso de uso de consulta do conteudo aprovado."""

        return GetScrapingResult(unit_of_work_factory=cls.create_unit_of_work)
