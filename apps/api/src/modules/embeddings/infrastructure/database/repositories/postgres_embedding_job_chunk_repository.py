"""Repositorio PostgreSQL para EmbeddingJobChunk."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.modules.embeddings.domain.entities import EmbeddingJobChunk
from apps.api.src.modules.embeddings.domain.repositories import (
    EmbeddingJobChunkRepository,
)
from apps.api.src.modules.embeddings.infrastructure.database.mappers.embedding_job_chunk_mapper import (
    EmbeddingJobChunkMapper,
)
from apps.api.src.modules.embeddings.infrastructure.database.models.embedding_job_chunk_model import (
    EmbeddingJobChunkModel,
)


class PostgresEmbeddingJobChunkRepository(EmbeddingJobChunkRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, chunk: EmbeddingJobChunk) -> None:
        model = await self._session.get(EmbeddingJobChunkModel, chunk.id)
        if model is None:
            self._session.add(EmbeddingJobChunkMapper.to_model(chunk))
        else:
            EmbeddingJobChunkMapper.update_model(model, chunk)
        await self._session.flush()

    async def list_by_job_id(self, job_id: UUID) -> list[EmbeddingJobChunk]:
        models = await self._session.scalars(
            select(EmbeddingJobChunkModel)
            .where(EmbeddingJobChunkModel.job_id == job_id)
            .order_by(EmbeddingJobChunkModel.created_at)
        )
        return [EmbeddingJobChunkMapper.to_entity(m) for m in models]
