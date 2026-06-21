"""Schemas Pydantic do modulo startups."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api.src.modules.startups.application.dto import (
    StartupEvidenceView,
    StartupView,
)
from apps.api.src.modules.startups.domain.enums import StartupEvidenceType


class CreateStartupRequest(BaseModel):
    name: str
    website_url: str | None = None
    description: str | None = None
    sector: str | None = None
    country: str | None = None


class UpdateStartupRequest(BaseModel):
    name: str | None = None
    website_url: str | None = None
    description: str | None = None
    sector: str | None = None
    country: str | None = None


class AddStartupEvidenceRequest(BaseModel):
    scraping_result_id: UUID
    source_url: str
    evidence_type: StartupEvidenceType = StartupEvidenceType.OTHER
    title: str | None = None
    confidence_score: float | None = None
    notes: str | None = None


class StartupResponse(BaseModel):
    id: UUID
    name: str
    website_url: str | None
    description: str | None
    sector: str | None
    country: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_view(cls, view: StartupView) -> "StartupResponse":
        return cls(
            id=view.id,
            name=view.name,
            website_url=view.website_url,
            description=view.description,
            sector=view.sector,
            country=view.country,
            created_at=view.created_at,
            updated_at=view.updated_at,
        )


class StartupEvidenceResponse(BaseModel):
    id: UUID
    startup_id: UUID
    scraping_result_id: UUID
    source_url: str
    evidence_type: str
    title: str | None
    confidence_score: float | None
    notes: str | None
    created_at: datetime

    @classmethod
    def from_view(cls, view: StartupEvidenceView) -> "StartupEvidenceResponse":
        return cls(
            id=view.id,
            startup_id=view.startup_id,
            scraping_result_id=view.scraping_result_id,
            source_url=view.source_url,
            evidence_type=view.evidence_type.value,
            title=view.title,
            confidence_score=view.confidence_score,
            notes=view.notes,
            created_at=view.created_at,
        )
