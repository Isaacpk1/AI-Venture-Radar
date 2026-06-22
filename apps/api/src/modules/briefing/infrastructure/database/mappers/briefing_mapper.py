"""Mapper entre Briefing e BriefingModel."""

from apps.api.src.modules.briefing.domain.entities import Briefing
from apps.api.src.modules.briefing.infrastructure.database.models.briefing_model import (
    BriefingModel,
)


class BriefingMapper:

    @staticmethod
    def to_model(entity: Briefing) -> BriefingModel:
        return BriefingModel(
            id=entity.id,
            startup_id=entity.startup_id,
            content=entity.content,
            generated_at=entity.generated_at,
        )

    @staticmethod
    def to_entity(model: BriefingModel) -> Briefing:
        return Briefing(
            id=model.id,
            startup_id=model.startup_id,
            content=model.content,
            generated_at=model.generated_at,
        )
