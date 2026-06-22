"""Testes das invariantes da entidade Recommendation."""

from uuid import uuid4

import pytest

from apps.api.src.modules.recommendations.domain.entities import Recommendation
from apps.api.src.modules.recommendations.domain.exceptions import RecommendationError


def _build(**overrides) -> Recommendation:
    defaults = {
        "startup_id": uuid4(),
        "technology_slug": "NVIDIA-NIM",
        "technology_name": "NVIDIA NIM",
        "category": "model_serving",
        "score": 0.8,
        "justification": "Evidencias mencionam llm e inference.",
    }
    defaults.update(overrides)
    return Recommendation(**defaults)


def test_recommendation_normalizes_slug_to_lowercase() -> None:
    recommendation = _build()

    assert recommendation.technology_slug == "nvidia-nim"


def test_recommendation_rejects_score_above_one() -> None:
    with pytest.raises(RecommendationError):
        _build(score=1.5)


def test_recommendation_rejects_negative_score() -> None:
    with pytest.raises(RecommendationError):
        _build(score=-0.1)


def test_recommendation_rejects_empty_justification() -> None:
    with pytest.raises(RecommendationError):
        _build(justification="   ")


def test_recommendation_rejects_empty_technology_slug() -> None:
    with pytest.raises(RecommendationError):
        _build(technology_slug="   ")
