"""Testes do caso de uso UpsertChunkEmbedding."""

from uuid import uuid4

import pytest

from apps.api.src.modules.embeddings.application.dto import (
    ChunkEmbeddingRecord,
    ChunkSearchResult,
    UpsertChunkEmbeddingInput,
)
from apps.api.src.modules.embeddings.application.public.vector_repository import (
    VectorRepository,
)
from apps.api.src.modules.embeddings.application.use_cases.generate_chunk_embedding import (
    GenerateChunkEmbedding,
)
from apps.api.src.modules.embeddings.application.use_cases.upsert_chunk_embedding import (
    UpsertChunkEmbedding,
)
from apps.api.src.modules.embeddings.infrastructure.fake.deterministic_fake_provider import (
    DeterministicFakeEmbeddingProvider,
)


class FakeVectorRepository(VectorRepository):
    def __init__(self) -> None:
        self.records: dict = {}

    async def upsert(self, record: ChunkEmbeddingRecord) -> None:
        self.records[record.chunk_id] = record

    async def search(
        self, query_vector: tuple[float, ...], *, limit: int = 5
    ) -> list[ChunkSearchResult]:
        return []


@pytest.mark.anyio
async def test_execute_generates_and_persists_embedding() -> None:
    vector_repository = FakeVectorRepository()
    use_case = UpsertChunkEmbedding(
        generate_chunk_embedding=GenerateChunkEmbedding(
            embedding_service=DeterministicFakeEmbeddingProvider()
        ),
        vector_repository=vector_repository,
    )
    chunk_id = uuid4()
    document_id = uuid4()

    await use_case.execute(
        UpsertChunkEmbeddingInput(
            chunk_id=chunk_id,
            document_id=document_id,
            source_url="https://startup.example.com",
            text="a NVIDIA recomenda NIM para servir LLMs",
        )
    )

    record = vector_repository.records[chunk_id]
    assert record.document_id == document_id
    assert record.source_url == "https://startup.example.com"
    assert len(record.values) == record.dimension
