"""Schemas Pydantic da presentation layer do módulo de ingestion."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api.src.modules.ingestion.application.dto import IngestionJobView


class CreateIngestionJobRequest(BaseModel):
    scraping_result_id: UUID


class IngestionJobResponse(BaseModel):
    id: UUID
    scraping_result_id: UUID
    status: str
    document_id: UUID | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_view(cls, view: IngestionJobView) -> "IngestionJobResponse":
        return cls(
            id=view.id,
            scraping_result_id=view.scraping_result_id,
            status=view.status.value,
            document_id=view.document_id,
            error_message=view.error_message,
            created_at=view.created_at,
            started_at=view.started_at,
            finished_at=view.finished_at,
        )
