"""DTOs do modulo recommendations."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class GenerateRecommendationsInput:
    startup_id: UUID


@dataclass(frozen=True)
class RecommendationView:
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


@dataclass(frozen=True)
class EvidenceSnapshot:
    """Evidencia de uma startup, no vocabulario de recommendations."""

    evidence_id: UUID
    title: str | None
    notes: str | None


@dataclass(frozen=True)
class StartupProfileSnapshot:
    """Perfil minimo de startup necessario para gerar recomendacoes."""

    sector: str | None
    description: str | None
    evidences: tuple[EvidenceSnapshot, ...]
    ai_maturity_level: str | None = None


@dataclass(frozen=True)
class NvidiaTechnologySnapshot:
    """Tecnologia NVIDIA, no vocabulario de recommendations."""

    slug: str
    name: str
    category: str
    use_cases: tuple[str, ...]
    keywords: tuple[str, ...]
