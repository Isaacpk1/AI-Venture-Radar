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


class IngestedDocumentReader(ABC):
    """Permite que outros modulos consultem documentos ja ingeridos."""

    @abstractmethod
    async def get_by_scraping_result_id(
        self, scraping_result_id: UUID
    ) -> IngestedDocumentSummary | None:
        """Retorna o sumario do documento ingerido ou ``None``."""
