"""DTOs do modulo startup_discovery."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from apps.api.src.modules.startup_discovery.domain.enums import DiscoveryRunStatus


@dataclass(frozen=True)
class SubmittedUrlView:
    hub_name: str
    url: str
    job_id: UUID


@dataclass(frozen=True)
class DiscoveryRunView:
    id: UUID
    status: DiscoveryRunStatus
    hubs_processed: int
    urls_found: int
    jobs_submitted: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    submitted_urls: list[SubmittedUrlView] = field(default_factory=list)
