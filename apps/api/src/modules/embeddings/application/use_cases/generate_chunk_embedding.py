"""Caso de uso para gerar o embedding de um chunk."""

from apps.api.src.modules.embeddings.application.dto import (
    ChunkEmbeddingView,
    GenerateChunkEmbeddingInput,
)
from apps.api.src.modules.embeddings.application.public.embedding_service import (
    EmbeddingService,
)
from apps.api.src.modules.embeddings.domain.exceptions import EmptyChunkTextError


class GenerateChunkEmbedding:
    """Gera o vetor de embedding de um chunk usando o EmbeddingService injetado."""

    def __init__(self, *, embedding_service: EmbeddingService) -> None:
        self._embedding_service = embedding_service

    async def execute(
        self, embedding_input: GenerateChunkEmbeddingInput
    ) -> ChunkEmbeddingView:
        if not embedding_input.text.strip():
            raise EmptyChunkTextError(
                f"Chunk {embedding_input.chunk_id} tem texto vazio."
            )
        return await self._embedding_service.embed(embedding_input)
