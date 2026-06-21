"""Contrato publico para outros modulos lerem documentos ingeridos.

Outros modulos (ex: embeddings, RAG) importam apenas este contrato,
nunca as entidades ou repositorios internos do modulo de ingestion.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class IngestedDocumentSummary:
    id: UUID
    scraping_result_id: UUID
    url: str
    title: str | None
    word_count: int
    chunk_count: int


@dataclass
class ChunkRecord:
    """Chunk pronto para embedding, com a URL de origem do documento."""

    id: UUID
    document_id: UUID
    text: str
    source_url: str


class IngestedDocumentReader(ABC):
    """Permite que outros modulos consultem documentos ja ingeridos."""

    @abstractmethod
    async def get_by_scraping_result_id(
        self, scraping_result_id: UUID
    ) -> IngestedDocumentSummary | None:
        """Retorna o sumario do documento ingerido ou ``None``."""

    @abstractmethod
    async def list_chunks_by_document_id(
        self, document_id: UUID
    ) -> list[ChunkRecord]:
        """Retorna todos os chunks de um documento, ordenados por posicao."""
