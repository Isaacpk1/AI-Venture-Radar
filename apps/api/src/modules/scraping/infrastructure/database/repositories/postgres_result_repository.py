"""Implementação PostgreSQL do contrato ``ScrapingResultRepository``."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.modules.scraping.domain.entities import ScrapingResult
from apps.api.src.modules.scraping.domain.repositories import (
    ScrapingResultRepository,
)
from apps.api.src.modules.scraping.infrastructure.database.mappers.scraping_result_mapper import (
    ScrapingResultMapper,
)
from apps.api.src.modules.scraping.infrastructure.database.models import (
    ScrapingResultModel,
)


class PostgresScrapingResultRepository(ScrapingResultRepository):
    """Persiste e consulta resultados aprovados no PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, result: ScrapingResult) -> None:
        """Insere um resultado novo ou atualiza o registro existente."""

        model = await self.session.get(ScrapingResultModel, result.id)

        if model is None:
            self.session.add(ScrapingResultMapper.to_model(result))
        else:
            ScrapingResultMapper.update_model(model, result)

        await self.session.flush()

    async def get_by_id(self, result_id: UUID) -> ScrapingResult | None:
        """Consulta um resultado pelo identificador primário."""

        model = await self.session.get(ScrapingResultModel, result_id)
        if model is None:
            return None

        return ScrapingResultMapper.to_entity(model)

    async def get_by_content_hash(
        self,
        content_hash: str,
    ) -> ScrapingResult | None:
        """Consulta um resultado que possua o mesmo hash de conteúdo."""

        model = await self.session.scalar(
            select(ScrapingResultModel).where(
                ScrapingResultModel.content_hash == content_hash
            )
        )
        if model is None:
            return None

        return ScrapingResultMapper.to_entity(model)
