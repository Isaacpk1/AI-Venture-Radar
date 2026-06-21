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


@dataclass
class UpsertChunkEmbeddingInput:
    chunk_id: UUID
    document_id: UUID
    source_url: str
    text: str


@dataclass
class ChunkEmbeddingRecord:
    chunk_id: UUID
    document_id: UUID
    source_url: str
    values: tuple[float, ...]
    dimension: int
    model_name: str


@dataclass
class ChunkSearchResult:
    chunk_id: UUID
    document_id: UUID
    source_url: str
    score: float
