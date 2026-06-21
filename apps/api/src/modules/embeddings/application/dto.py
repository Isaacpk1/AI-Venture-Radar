"""DTOs do modulo embeddings."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class GenerateChunkEmbeddingInput:
    chunk_id: UUID
    text: str


@dataclass
class ChunkEmbeddingView:
    chunk_id: UUID
    values: tuple[float, ...]
    dimension: int
    model_name: str
