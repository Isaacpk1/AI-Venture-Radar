"""Schemas Pydantic do modulo briefing."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api.src.modules.briefing.application.dto import BriefingView


class GenerateBriefingRequest(BaseModel):
    startup_id: UUID


class BriefingResponse(BaseModel):
    id: UUID
    startup_id: UUID
    content: str
    generated_at: datetime

    @classmethod
    def from_view(cls, view: BriefingView) -> "BriefingResponse":
        return cls(
            id=view.id,
            startup_id=view.startup_id,
            content=view.content,
            generated_at=view.generated_at,
        )
