"""Composicao das dependencias concretas do modulo startup_discovery."""

from apps.api.src.config.settings import get_settings
from apps.api.src.modules.orchestration.factories.orchestration_factory import (
    OrchestrationFactory,
)
from apps.api.src.modules.startup_discovery.application.use_cases.get_discovery_run import (
    GetDiscoveryRun,
)
from apps.api.src.modules.startup_discovery.application.use_cases.run_discovery import (
    RunStartupDiscovery,
)
from apps.api.src.modules.startup_discovery.infrastructure.database.postgres_unit_of_work import (
    PostgresDiscoveryUnitOfWork,
)
from apps.api.src.modules.startup_discovery.infrastructure.hub_extractors.abstartups import (
    AbstartupsExtractor,
)
from apps.api.src.modules.startup_discovery.infrastructure.hub_extractors.inovativa import (
    InovativaBrasilExtractor,
)
from apps.api.src.modules.startup_discovery.infrastructure.hub_extractors.open_startups import (
    OpenStartupsExtractor,
)
from apps.api.src.modules.startup_discovery.infrastructure.orchestration_adapters.url_ingestion_adapter import (
    StartupDiscoveryUrlIngestionAdapter,
)


def _extractors() -> dict:
    return {
        "inovativa": InovativaBrasilExtractor(),
        "abstartups": AbstartupsExtractor(),
        "open_startups": OpenStartupsExtractor(),
    }


class StartupDiscoveryFactory:

    @staticmethod
    def create_run_discovery() -> RunStartupDiscovery:
        settings = get_settings()
        return RunStartupDiscovery(
            uow_factory=PostgresDiscoveryUnitOfWork,
            extractors=_extractors(),
            url_ingestion_submitter=StartupDiscoveryUrlIngestionAdapter(
                OrchestrationFactory.create_create_url_ingestion_job()
            ),
            max_per_run=settings.startup_discovery_max_per_run,
        )

    @staticmethod
    def create_get_discovery_run() -> GetDiscoveryRun:
        return GetDiscoveryRun(PostgresDiscoveryUnitOfWork)
