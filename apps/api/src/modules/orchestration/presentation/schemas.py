"""Schemas Pydantic do modulo orchestration."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api.src.modules.orchestration.application.dto import AnalysisJobView


class CreateAnalysisJobRequest(BaseModel):
    startup_id: UUID


class AnalysisJobResponse(BaseModel):
    id: UUID
    startup_id: UUID
    status: str
    recommendation_count: int | None
    briefing_id: UUID | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_view(cls, view: AnalysisJobView) -> "AnalysisJobResponse":
        return cls(
            id=view.id,
            startup_id=view.startup_id,
            status=view.status.value,
            recommendation_count=view.recommendation_count,
            briefing_id=view.briefing_id,
            error_message=view.error_message,
            created_at=view.created_at,
            started_at=view.started_at,
            finished_at=view.finished_at,
        )
