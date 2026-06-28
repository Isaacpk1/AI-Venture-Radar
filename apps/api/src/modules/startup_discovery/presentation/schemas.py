"""Schemas Pydantic da presentation layer do modulo startup_discovery."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api.src.modules.startup_discovery.domain.enums import DiscoveryRunStatus


class SubmittedUrlResponse(BaseModel):
    hub_name: str
    url: str
    job_id: UUID


class DiscoveryRunResponse(BaseModel):
    id: UUID
    status: DiscoveryRunStatus
    hubs_processed: int
    urls_found: int
    jobs_submitted: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    submitted_urls: list[SubmittedUrlResponse] = []
