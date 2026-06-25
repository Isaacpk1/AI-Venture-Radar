"""Repositorio PostgreSQL para DiscoveryRun."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.modules.startup_discovery.domain.entities import DiscoveryRun
from apps.api.src.modules.startup_discovery.domain.repositories import (
    DiscoveryRunRepository,
)
from apps.api.src.modules.startup_discovery.infrastructure.database.mappers.discovery_run_mapper import (
    DiscoveryRunMapper,
)
from apps.api.src.modules.startup_discovery.infrastructure.database.models.discovery_run_model import (
    DiscoveryRunModel,
)


class PostgresDiscoveryRunRepository(DiscoveryRunRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, run: DiscoveryRun) -> None:
        model = await self._session.get(DiscoveryRunModel, run.id)
        if model is None:
            self._session.add(DiscoveryRunMapper.to_model(run))
        else:
            DiscoveryRunMapper.update_model(model, run)
        await self._session.flush()

    async def get_by_id(self, run_id: UUID) -> DiscoveryRun | None:
        model = await self._session.get(DiscoveryRunModel, run_id)
        if model is None:
            return None
        return DiscoveryRunMapper.to_entity(model)

    async def list_recent(self, *, limit: int = 20) -> list[DiscoveryRun]:
        statement = (
            select(DiscoveryRunModel)
            .order_by(DiscoveryRunModel.created_at.desc())
            .limit(limit)
        )
        models = (await self._session.scalars(statement)).all()
        return [DiscoveryRunMapper.to_entity(m) for m in models]
