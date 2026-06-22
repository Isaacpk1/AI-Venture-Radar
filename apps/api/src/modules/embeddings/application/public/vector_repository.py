"""Contrato publico de persistencia e busca vetorial.

Outro arquivo que outros modulos (ex: RAG) podem importar diretamente — o
RAG vai chamar ``search()`` para recuperar chunks semanticamente
relevantes. ``upsert()`` e usado internamente pelo proprio modulo
embeddings (``UpsertChunkEmbedding``). A implementacao concreta hoje (V3) e'
``infrastructure/qdrant/qdrant_vector_repository.py``, escolhida por
``factories/embeddings_factory.py``.
"""

from abc import ABC, abstractmethod

from apps.api.src.modules.embeddings.application.dto import (
    ChunkEmbeddingRecord,
    ChunkSearchResult,
)


class VectorRepository(ABC):
    """Persiste e busca vetores de chunks."""

    @abstractmethod
    async def upsert(self, record: ChunkEmbeddingRecord) -> None:
        """Insere ou atualiza o vetor de um chunk."""

    @abstractmethod
    async def search(
        self,
        query_vector: tuple[float, ...],
        *,
        limit: int = 5,
        source_type: str | None = None,
    ) -> list[ChunkSearchResult]:
        """Busca os chunks mais proximos do vetor de consulta informado."""
