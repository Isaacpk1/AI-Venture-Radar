"""Entidades do modulo startup_discovery."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from apps.api.src.modules.startup_discovery.domain.enums import DiscoveryRunStatus
from apps.api.src.modules.startup_discovery.domain.exceptions import (
    InvalidDiscoveryRunTransitionError,
)


class DiscoveryRun:
    """Representa uma execucao de descoberta de startups em hubs publicos."""

    def __init__(
        self,
        *,
        id: UUID | None = None,
        status: DiscoveryRunStatus = DiscoveryRunStatus.PENDING,
        hubs_processed: int = 0,
        urls_found: int = 0,
        jobs_submitted: int = 0,
        error_message: str | None = None,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        self.id: UUID = id or uuid4()
        self.status = status
        self.hubs_processed = hubs_processed
        self.urls_found = urls_found
        self.jobs_submitted = jobs_submitted
        self.error_message = error_message
        self.created_at: datetime = created_at or datetime.now(timezone.utc)
        self.completed_at = completed_at

    def start(self) -> None:
        if self.status is not DiscoveryRunStatus.PENDING:
            raise InvalidDiscoveryRunTransitionError(
                f"Nao e possivel iniciar um DiscoveryRun em status {self.status.value}."
            )
        self.status = DiscoveryRunStatus.RUNNING

    def complete(
        self, *, hubs_processed: int, urls_found: int, jobs_submitted: int
    ) -> None:
        if self.status is not DiscoveryRunStatus.RUNNING:
            raise InvalidDiscoveryRunTransitionError(
                f"Nao e possivel completar um DiscoveryRun em status {self.status.value}."
            )
        self.status = DiscoveryRunStatus.COMPLETED
        self.hubs_processed = hubs_processed
        self.urls_found = urls_found
        self.jobs_submitted = jobs_submitted
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, reason: str) -> None:
        if self.status is not DiscoveryRunStatus.RUNNING:
            raise InvalidDiscoveryRunTransitionError(
                f"Nao e possivel falhar um DiscoveryRun em status {self.status.value}."
            )
        self.status = DiscoveryRunStatus.FAILED
        self.error_message = reason
        self.completed_at = datetime.now(timezone.utc)
