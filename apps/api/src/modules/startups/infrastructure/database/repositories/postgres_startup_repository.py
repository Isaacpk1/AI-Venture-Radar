"""Repositorio PostgreSQL para Startup."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.modules.startups.domain.entities import Startup
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
