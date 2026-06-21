"""Testes da composicao de dependencias do modulo embeddings."""

from uuid import uuid4

import pytest

from apps.api.src.modules.embeddings.application.dto import GenerateChunkEmbeddingInput
from apps.api.src.modules.embeddings.application.use_cases.generate_chunk_embedding import (
    GenerateChunkEmbedding,
)
from apps.api.src.modules.embeddings.factories.embeddings_factory import EmbeddingsFactory
from apps.api.src.modules.embeddings.infrastructure.fake.deterministic_fake_provider import (
    DeterministicFakeEmbeddingProvider,
)


def test_create_embedding_service_returns_fake_provider() -> None:
    service = EmbeddingsFactory.create_embedding_service()

    assert isinstance(service, DeterministicFakeEmbeddingProvider)


def test_create_generate_chunk_embedding_returns_use_case() -> None:
    use_case = EmbeddingsFactory.create_generate_chunk_embedding()

    assert isinstance(use_case, GenerateChunkEmbedding)


@pytest.mark.anyio
async def test_create_generate_chunk_embedding_wires_dependency_end_to_end() -> None:
    use_case = EmbeddingsFactory.create_generate_chunk_embedding()

    view = await use_case.execute(
        GenerateChunkEmbeddingInput(chunk_id=uuid4(), text="texto valido")
    )

    assert len(view.values) == view.dimension
