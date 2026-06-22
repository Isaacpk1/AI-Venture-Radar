"""Portas que conectam a aplicacao de RAG a tecnologias externas.

A aplicacao precisa de busca lexical e reranking, mas nao deve conhecer
SQL textual contra `chunks` (de `ingestion`) nem o SDK do Cohere
diretamente.
"""

from abc import ABC, abstractmethod

from apps.api.src.modules.rag.application.dto import (
    EvidenceChunkView,
    LexicalSearchResult,
)


class LexicalSearchRepository(ABC):
    """Busca lexical (full-text) sobre o texto dos chunks."""

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        limit: int,
        source_type: str | None = None,
    ) -> list[LexicalSearchResult]:
        """Busca chunks por relevancia lexical a partir da query."""


class Reranker(ABC):
    """Reordena evidencias recuperadas por relevancia semantica a query."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        evidences: list[EvidenceChunkView],
        *,
        top_n: int,
    ) -> list[EvidenceChunkView]:
        """Reordena e corta as evidencias para as `top_n` mais relevantes."""
