"""DTOs do modulo briefing."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class GenerateBriefingInput:
    startup_id: UUID


@dataclass(frozen=True)
class BriefingView:
    id: UUID
    startup_id: UUID
    content: str
    generated_at: datetime


@dataclass(frozen=True)
class StartupSnapshot:
    """Perfil da startup, no vocabulario de briefing."""

    name: str
    sector: str | None
    description: str | None
    country: str | None
    website_url: str | None


@dataclass(frozen=True)
class EvidenceSnapshot:
    """Evidencia da startup, no vocabulario de briefing."""

    title: str | None
    source_url: str
    evidence_type: str
    confidence_score: float | None


@dataclass(frozen=True)
class StartupProfileSnapshot:
    """Perfil completo (startup + evidencias), no vocabulario de briefing."""

    startup: StartupSnapshot
    evidences: tuple[EvidenceSnapshot, ...]


@dataclass(frozen=True)
class RecommendationSnapshot:
    """Recomendacao NVIDIA, no vocabulario de briefing."""

    technology_name: str
    category: str
    score: float
    justification: str
