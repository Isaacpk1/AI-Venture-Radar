"""Contratos de persistencia do modulo de embeddings."""

from abc import ABC, abstractmethod
from uuid import UUID

from apps.api.src.modules.embeddings.domain.entities import (
    EmbeddingJob,
    EmbeddingJobChunk,
)


class EmbeddingJobRepository(ABC):

    @abstractmethod
    async def save(self, job: EmbeddingJob) -> None:
        """Cria ou atualiza um job."""

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> EmbeddingJob | None:
        """Retorna o job ou ``None``."""


class EmbeddingJobChunkRepository(ABC):

    @abstractmethod
    async def save(self, chunk: EmbeddingJobChunk) -> None:
        """Cria ou atualiza o status de um chunk dentro de um job."""

    @abstractmethod
    async def list_by_job_id(self, job_id: UUID) -> list[EmbeddingJobChunk]:
        """Lista todos os chunks rastreados de um job."""
