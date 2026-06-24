"""Repositorio PostgreSQL para Startup."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.modules.startups.domain.entities import Startup
from apps.api.src.modules.startups.domain.enums import AiMaturityLevel
from apps.api.src.modules.startups.domain.repositories import StartupRepository
from apps.api.src.modules.startups.infrastructure.database.mappers.startup_mapper import (
    StartupMapper,
)
from apps.api.src.modules.startups.infrastructure.database.models.startup_model import (
    StartupModel,
)


class PostgresStartupRepository(StartupRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, startup: Startup) -> None:
        model = await self._session.get(StartupModel, startup.id)
        if model is None:
            self._session.add(StartupMapper.to_model(startup))
        else:
            StartupMapper.update_model(model, startup)
        await self._session.flush()

    async def get_by_id(self, startup_id: UUID) -> Startup | None:
        model = await self._session.get(StartupModel, startup_id)
        if model is None:
            return None
        return StartupMapper.to_entity(model)

    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        query: str | None = None,
        sector: str | None = None,
        country: str | None = None,
        ai_maturity_level: AiMaturityLevel | None = None,
    ) -> tuple[list[Startup], int]:
        filters = []
        if query:
            pattern = f"%{query.strip()}%"
            filters.append(
                or_(
                    StartupModel.name.ilike(pattern),
                    StartupModel.description.ilike(pattern),
                )
            )
        if sector:
            filters.append(StartupModel.sector.ilike(sector.strip()))
        if country:
            filters.append(StartupModel.country.ilike(country.strip()))
        if ai_maturity_level is not None:
            filters.append(StartupModel.ai_maturity_level == ai_maturity_level.value)

        statement = (
            select(StartupModel)
            .where(*filters)
            .order_by(StartupModel.updated_at.desc(), StartupModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count()).select_from(StartupModel).where(*filters)
        models = (await self._session.scalars(statement)).all()
        total = await self._session.scalar(count_statement)
        return [StartupMapper.to_entity(model) for model in models], total or 0
