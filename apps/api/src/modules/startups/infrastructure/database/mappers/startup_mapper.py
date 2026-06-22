"""Mapper entre Startup e StartupModel."""

from apps.api.src.modules.startups.domain.entities import Startup
from apps.api.src.modules.startups.domain.enums import AiMaturityLevel, FundingStage
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
            ai_maturity_level=(
                entity.ai_maturity_level.value
                if entity.ai_maturity_level is not None
                else None
            ),
            classification_reason=entity.classification_reason,
            classified_at=entity.classified_at,
            founders=list(entity.founders),
            funding_stage=(
                entity.funding_stage.value if entity.funding_stage is not None else None
            ),
            funding_amount_usd=entity.funding_amount_usd,
            customers=list(entity.customers),
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
            ai_maturity_level=(
                AiMaturityLevel(model.ai_maturity_level)
                if model.ai_maturity_level is not None
                else None
            ),
            classification_reason=model.classification_reason,
            classified_at=model.classified_at,
            founders=tuple(model.founders),
            funding_stage=(
                FundingStage(model.funding_stage)
                if model.funding_stage is not None
                else None
            ),
            funding_amount_usd=model.funding_amount_usd,
            customers=tuple(model.customers),
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
        model.ai_maturity_level = (
            entity.ai_maturity_level.value
            if entity.ai_maturity_level is not None
            else None
        )
        model.classification_reason = entity.classification_reason
        model.classified_at = entity.classified_at
        model.founders = list(entity.founders)
        model.funding_stage = (
            entity.funding_stage.value if entity.funding_stage is not None else None
        )
        model.funding_amount_usd = entity.funding_amount_usd
        model.customers = list(entity.customers)
        model.updated_at = entity.updated_at
