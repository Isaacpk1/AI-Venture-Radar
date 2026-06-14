"""Implementação PostgreSQL do contrato ``ScrapingAttemptRepository``."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.modules.scraping.domain.entities import ScrapingAttempt
from apps.api.src.modules.scraping.domain.repositories import (
    ScrapingAttemptRepository,
)
from apps.api.src.modules.scraping.infrastructure.database.mappers.scraping_attempt_mapper import (
    ScrapingAttemptMapper,
)
from apps.api.src.modules.scraping.infrastructure.database.models import (
    ScrapingAttemptModel,
)


class PostgresScrapingAttemptRepository(ScrapingAttemptRepository):
    """Persiste e consulta tentativas usando SQLAlchemy assíncrono."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, attempt: ScrapingAttempt) -> None:
        """Insere uma tentativa nova ou atualiza seu estado."""

        model = await self.session.get(ScrapingAttemptModel, attempt.id)

        if model is None:
            self.session.add(ScrapingAttemptMapper.to_model(attempt))
        else:
            ScrapingAttemptMapper.update_model(model, attempt)

        await self.session.flush()

    async def list_by_job_id(self, job_id: UUID) -> list[ScrapingAttempt]:
        """Lista as tentativas de um job na ordem em que começaram."""

        result = await self.session.scalars(
            select(ScrapingAttemptModel)
            .where(ScrapingAttemptModel.job_id == job_id)
            .order_by(ScrapingAttemptModel.started_at.asc())
        )

        return [
            ScrapingAttemptMapper.to_entity(model)
            for model in result.all()
        ]
