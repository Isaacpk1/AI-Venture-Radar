"""Caso de uso para criar startup."""

from uuid import UUID

from apps.api.src.modules.startups.application.dto import (
    CreateStartupInput,
    StartupView,
)
from apps.api.src.modules.startups.application.public.startup_creator import (
    StartupCreator,
)
from apps.api.src.modules.startups.application.unit_of_work import (
    StartupsUnitOfWorkFactory,
)
from apps.api.src.modules.startups.domain.entities import Startup


class CreateStartup(StartupCreator):
    """Cria uma startup no repositorio relacional."""

    def __init__(self, uow_factory: StartupsUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create_startup(
        self, *, name: str, website_url: str | None = None
    ) -> UUID:
        view = await self.execute(
            CreateStartupInput(name=name, website_url=website_url)
        )
        return view.id

    async def execute(self, startup_input: CreateStartupInput) -> StartupView:
        startup = Startup(
            name=startup_input.name,
            website_url=startup_input.website_url,
            description=startup_input.description,
            sector=startup_input.sector,
            country=startup_input.country,
        )

        async with self._uow_factory() as uow:
            await uow.startup_repository.save(startup)
            await uow.commit()

        return to_startup_view(startup)


def to_startup_view(startup: Startup) -> StartupView:
    return StartupView(
        id=startup.id,
        name=startup.name,
        website_url=startup.website_url,
        description=startup.description,
        sector=startup.sector,
        country=startup.country,
        ai_maturity_level=startup.ai_maturity_level,
        classification_reason=startup.classification_reason,
        classified_at=startup.classified_at,
        founders=list(startup.founders),
        funding_stage=startup.funding_stage,
        funding_amount_usd=startup.funding_amount_usd,
        customers=list(startup.customers),
        created_at=startup.created_at,
        updated_at=startup.updated_at,
    )
