"""Schemas Pydantic do modulo recommendations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api.src.modules.recommendations.application.dto import RecommendationView


class GenerateRecommendationsRequest(BaseModel):
    startup_id: UUID


class RecommendationResponse(BaseModel):
    id: UUID
    startup_id: UUID
    technology_slug: str
    technology_name: str
    category: str
    score: float
    justification: str
    matched_keywords: list[str]
    evidence_ids: list[UUID]
    created_at: datetime

    @classmethod
    def from_view(cls, view: RecommendationView) -> "RecommendationResponse":
        return cls(
            id=view.id,
            startup_id=view.startup_id,
            technology_slug=view.technology_slug,
            technology_name=view.technology_name,
            category=view.category,
            score=view.score,
            justification=view.justification,
            matched_keywords=view.matched_keywords,
            evidence_ids=view.evidence_ids,
            created_at=view.created_at,
        )
