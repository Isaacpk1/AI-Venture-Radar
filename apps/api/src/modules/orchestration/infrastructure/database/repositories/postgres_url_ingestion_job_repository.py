"""Repositorio PostgreSQL para UrlIngestionJob."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.modules.orchestration.domain.entities import UrlIngestionJob
from apps.api.src.modules.orchestration.domain.repositories import (
    UrlIngestionJobRepository,
)
from apps.api.src.modules.orchestration.infrastructure.database.mappers.url_ingestion_job_mapper import (
    UrlIngestionJobMapper,
)
from apps.api.src.modules.orchestration.infrastructure.database.models.url_ingestion_job_model import (
    UrlIngestionJobModel,
)


class PostgresUrlIngestionJobRepository(UrlIngestionJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: UrlIngestionJob) -> None:
        model = await self._session.get(UrlIngestionJobModel, job.id)
        if model is None:
            self._session.add(UrlIngestionJobMapper.to_model(job))
        else:
            UrlIngestionJobMapper.update_model(model, job)
        await self._session.flush()

    async def get_by_id(self, job_id: UUID) -> UrlIngestionJob | None:
        model = await self._session.get(UrlIngestionJobModel, job_id)
        if model is None:
            return None
        return UrlIngestionJobMapper.to_entity(model)
