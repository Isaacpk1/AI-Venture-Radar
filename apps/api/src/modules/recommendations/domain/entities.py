"""Entidades do dominio do modulo recommendations."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from apps.api.src.modules.recommendations.domain.exceptions import (
    RecommendationError,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Recommendation:
    """Tecnologia NVIDIA recomendada para uma startup, com justificativa."""

    startup_id: UUID
    technology_slug: str
    technology_name: str
    category: str
    score: float
    justification: str
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)
    evidence_ids: tuple[UUID, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    complexity: str = "medium"

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.technology_slug = self.technology_slug.strip().lower()
        self.technology_name = self.technology_name.strip()
        self.category = self.category.strip()
        self.justification = self.justification.strip()
        self.complexity = self.complexity.strip().lower()

        if not self.technology_slug:
            raise RecommendationError("Recomendacao precisa ter technology_slug.")
        if not self.technology_name:
            raise RecommendationError("Recomendacao precisa ter technology_name.")
        if not self.justification:
            raise RecommendationError("Recomendacao precisa ter justificativa.")
        if not 0 <= self.score <= 1:
            raise RecommendationError("score deve ficar entre 0 e 1.")
        if not 0 <= self.confidence <= 1:
            raise RecommendationError("confidence deve ficar entre 0 e 1.")
        if self.complexity not in {"low", "medium", "high"}:
            raise RecommendationError("complexity deve ser low, medium ou high.")

    def update_justification(self, text: str) -> None:
        """Substitui a justificativa (ex: revisao de linguagem via agente)."""

        text = text.strip()
        if not text:
            raise RecommendationError("Recomendacao precisa ter justificativa.")
        self.justification = text
