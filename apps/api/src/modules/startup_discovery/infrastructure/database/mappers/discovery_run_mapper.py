"""Mapper entre DiscoveryRun (dominio) e DiscoveryRunModel (SQLAlchemy)."""

from apps.api.src.modules.startup_discovery.domain.entities import DiscoveryRun
from apps.api.src.modules.startup_discovery.domain.enums import DiscoveryRunStatus
from apps.api.src.modules.startup_discovery.infrastructure.database.models.discovery_run_model import (
    DiscoveryRunModel,
)


class DiscoveryRunMapper:

    @staticmethod
    def to_model(run: DiscoveryRun) -> DiscoveryRunModel:
        return DiscoveryRunModel(
            id=run.id,
            status=run.status.value,
            hubs_processed=run.hubs_processed,
            urls_found=run.urls_found,
            jobs_submitted=run.jobs_submitted,
            error_message=run.error_message,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )

    @staticmethod
    def update_model(model: DiscoveryRunModel, run: DiscoveryRun) -> None:
        model.status = run.status.value
        model.hubs_processed = run.hubs_processed
        model.urls_found = run.urls_found
        model.jobs_submitted = run.jobs_submitted
        model.error_message = run.error_message
        model.completed_at = run.completed_at

    @staticmethod
    def to_entity(model: DiscoveryRunModel) -> DiscoveryRun:
        return DiscoveryRun(
            id=model.id,
            status=DiscoveryRunStatus(model.status),
            hubs_processed=model.hubs_processed,
            urls_found=model.urls_found,
            jobs_submitted=model.jobs_submitted,
            error_message=model.error_message,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )
