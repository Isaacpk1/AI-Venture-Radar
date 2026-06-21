"""DTOs do modulo startups."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from apps.api.src.modules.startups.domain.enums import StartupEvidenceType


@dataclass
class CreateStartupInput:
    name: str
    website_url: str | None = None
    description: str | None = None
    sector: str | None = None
    country: str | None = None


@dataclass
class UpdateStartupInput:
    startup_id: UUID
    name: str | None = None
    website_url: str | None = None
    description: str | None = None
    sector: str | None = None
    country: str | None = None


@dataclass
class AddStartupEvidenceInput:
    startup_id: UUID
    scraping_result_id: UUID
    source_url: str
    evidence_type: StartupEvidenceType = StartupEvidenceType.OTHER
    title: str | None = None
    confidence_score: float | None = None
    notes: str | None = None


@dataclass
class StartupView:
    id: UUID
    name: str
    website_url: str | None
    description: str | None
    sector: str | None
    country: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class StartupEvidenceView:
    id: UUID
    startup_id: UUID
    scraping_result_id: UUID
    source_url: str
    evidence_type: StartupEvidenceType
    title: str | None
    confidence_score: float | None
    notes: str | None
    created_at: datetime
