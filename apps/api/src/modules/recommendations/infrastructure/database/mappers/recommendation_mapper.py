"""Mapper entre Recommendation e RecommendationModel."""

from uuid import UUID

from apps.api.src.modules.recommendations.domain.entities import Recommendation
from apps.api.src.modules.recommendations.infrastructure.database.models.recommendation_model import (
    RecommendationModel,
)


class RecommendationMapper:

    @staticmethod
    def to_model(entity: Recommendation) -> RecommendationModel:
        return RecommendationModel(
            id=entity.id,
            startup_id=entity.startup_id,
            technology_slug=entity.technology_slug,
            technology_name=entity.technology_name,
            category=entity.category,
            score=entity.score,
            confidence=entity.confidence,
            complexity=entity.complexity,
            justification=entity.justification,
            matched_keywords=list(entity.matched_keywords),
            evidence_ids=[str(evidence_id) for evidence_id in entity.evidence_ids],
            created_at=entity.created_at,
        )

    @staticmethod
    def to_entity(model: RecommendationModel) -> Recommendation:
        return Recommendation(
            id=model.id,
            startup_id=model.startup_id,
            technology_slug=model.technology_slug,
            technology_name=model.technology_name,
            category=model.category,
            score=model.score,
            confidence=model.confidence,
            complexity=model.complexity,
            justification=model.justification,
            matched_keywords=tuple(model.matched_keywords),
            evidence_ids=tuple(UUID(value) for value in model.evidence_ids),
            created_at=model.created_at,
        )
