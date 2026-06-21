"""Entidades do dominio do modulo startups."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from apps.api.src.modules.startups.domain.enums import StartupEvidenceType
from apps.api.src.modules.startups.domain.exceptions import InvalidStartupDataError


def utc_now() -> datetime:
    return datetime.now(UTC)


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


@dataclass
class Startup:
    """Representacao relacional basica de uma startup."""

    name: str
    website_url: str | None = None
    description: str | None = None
    sector: str | None = None
    country: str | None = None

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.website_url = _normalize_optional(self.website_url)
        self.description = _normalize_optional(self.description)
        self.sector = _normalize_optional(self.sector)
        self.country = _normalize_optional(self.country)
        if not self.name:
            raise InvalidStartupDataError("Startup precisa ter nome.")

    def update(
        self,
        *,
        name: str | None = None,
        website_url: str | None = None,
        description: str | None = None,
        sector: str | None = None,
        country: str | None = None,
    ) -> None:
        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise InvalidStartupDataError("Startup precisa ter nome.")
            self.name = normalized_name
        if website_url is not None:
            self.website_url = _normalize_optional(website_url)
        if description is not None:
            self.description = _normalize_optional(description)
        if sector is not None:
            self.sector = _normalize_optional(sector)
        if country is not None:
            self.country = _normalize_optional(country)
        self.updated_at = utc_now()


@dataclass
class StartupEvidence:
    """Fonte aprovada associada a uma startup."""

    startup_id: UUID
    scraping_result_id: UUID
    source_url: str
    evidence_type: StartupEvidenceType = StartupEvidenceType.OTHER
    title: str | None = None
    confidence_score: float | None = None
    notes: str | None = None

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.source_url = self.source_url.strip()
        self.title = _normalize_optional(self.title)
        self.notes = _normalize_optional(self.notes)
        if not self.source_url:
            raise InvalidStartupDataError("Evidencia precisa ter source_url.")
        if self.confidence_score is not None and not 0 <= self.confidence_score <= 1:
            raise InvalidStartupDataError(
                "confidence_score deve ficar entre 0 e 1."
            )
