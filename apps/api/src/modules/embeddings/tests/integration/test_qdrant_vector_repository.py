"""Testes integrados do QdrantVectorRepository contra Qdrant real."""

from uuid import uuid4

import pytest

from apps.api.src.config.settings import get_settings
from apps.api.src.modules.embeddings.application.dto import ChunkEmbeddingRecord
from apps.api.src.modules.embeddings.infrastructure.qdrant.qdrant_vector_repository import (
    QdrantVectorRepository,
)


@pytest.mark.anyio
async def test_upsert_and_search_round_trip() -> None:
    settings = get_settings()
    collection_name = f"chunk_embeddings_test_{uuid4().hex}"
    repository = QdrantVectorRepository(
        url=settings.qdrant_url, collection_name=collection_name
    )

    chunk_id = uuid4()
    document_id = uuid4()
    values = (0.1, 0.2, 0.3, 0.4)

    try:
        await repository.upsert(
            ChunkEmbeddingRecord(
                chunk_id=chunk_id,
                document_id=document_id,
                source_url="https://startup.example.com",
                values=values,
                dimension=len(values),
                model_name="fake-test",
            )
        )

        results = await repository.search(values, limit=5)

        assert any(result.chunk_id == chunk_id for result in results)
        match = next(result for result in results if result.chunk_id == chunk_id)
        assert match.document_id == document_id
        assert match.source_url == "https://startup.example.com"
        assert match.score > 0.99
    finally:
        await repository._client.delete_collection(collection_name)
        await repository._client.close()
