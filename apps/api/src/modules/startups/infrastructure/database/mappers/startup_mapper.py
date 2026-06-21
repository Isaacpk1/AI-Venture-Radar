"""Mapper entre Startup e StartupModel."""

from apps.api.src.modules.startups.domain.entities import Startup
from apps.api.src.modules.startups.infrastructure.database.models.startup_model import (
    StartupModel,
)


class StartupMapper:

    @staticmethod
    def to_model(entity: Startup) -> StartupModel:
        return StartupModel(
            id=entity.id,
            name=entity.name,
            website_url=entity.website_url,
            description=entity.description,
            sector=entity.sector,
            country=entity.country,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def to_entity(model: StartupModel) -> Startup:
        return Startup(
            id=model.id,
            name=model.name,
            website_url=model.website_url,
            description=model.description,
            sector=model.sector,
            country=model.country,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def update_model(model: StartupModel, entity: Startup) -> None:
        model.name = entity.name
        model.website_url = entity.website_url
        model.description = entity.description
        model.sector = entity.sector
        model.country = entity.country
        model.updated_at = entity.updated_at
