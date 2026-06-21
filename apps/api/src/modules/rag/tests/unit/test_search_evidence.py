"""Testes do caso de uso SearchEvidence."""

from uuid import UUID, uuid4

import pytest

from apps.api.src.modules.embeddings.application.dto import (
    ChunkEmbeddingRecord,
    ChunkEmbeddingView,
    ChunkSearchResult,
    GenerateChunkEmbeddingInput,
)
from apps.api.src.modules.embeddings.application.public.embedding_service import (
    EmbeddingService,
)
from apps.api.src.modules.embeddings.application.public.vector_repository import (
    VectorRepository,
)
from apps.api.src.modules.embeddings.application.use_cases.generate_chunk_embedding import (
    GenerateChunkEmbedding,
)
from apps.api.src.modules.ingestion.application.public.ingested_reader import (
    ChunkRecord,
    IngestedDocumentReader,
    IngestedDocumentSummary,
)
from apps.api.src.modules.rag.application.dto import SearchEvidenceInput
from apps.api.src.modules.rag.application.use_cases.search_evidence import (
    SearchEvidence,
)
from apps.api.src.modules.rag.domain.exceptions import EmptyRagQueryError


class FakeEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        self.inputs: list[GenerateChunkEmbeddingInput] = []

    async def embed(
        self, embedding_input: GenerateChunkEmbeddingInput
    ) -> ChunkEmbeddingView:
        self.inputs.append(embedding_input)
        return ChunkEmbeddingView(
            chunk_id=embedding_input.chunk_id,
            values=(0.1, 0.2, 0.3),
            dimension=3,
            model_name="fake-rag",
        )


class FakeVectorRepository(VectorRepository):
    def __init__(self, results: list[ChunkSearchResult]) -> None:
        self.results = results
        self.searched_vectors: list[tuple[float, ...]] = []
        self.limits: list[int] = []

    async def upsert(self, record: ChunkEmbeddingRecord) -> None:
        pass

    async def search(
        self, query_vector: tuple[float, ...], *, limit: int = 5
    ) -> list[ChunkSearchResult]:
        self.searched_vectors.append(query_vector)
        self.limits.append(limit)
        return self.results[:limit]


class FakeIngestedDocumentReader(IngestedDocumentReader):
    def __init__(self, chunks_by_document: dict[UUID, list[ChunkRecord]]) -> None:
        self.chunks_by_document = chunks_by_document
        self.calls: list[UUID] = []

    async def get_by_scraping_result_id(
        self, scraping_result_id: UUID
    ) -> IngestedDocumentSummary | None:
        return None

    async def list_chunks_by_document_id(
        self, document_id: UUID
    ) -> list[ChunkRecord]:
        self.calls.append(document_id)
        return self.chunks_by_document.get(document_id, [])


def _make_use_case(
    *,
    vector_results: list[ChunkSearchResult],
    chunks_by_document: dict[UUID, list[ChunkRecord]],
) -> tuple[SearchEvidence, FakeEmbeddingService, FakeVectorRepository, FakeIngestedDocumentReader]:
    embedding_service = FakeEmbeddingService()
    vector_repository = FakeVectorRepository(vector_results)
    reader = FakeIngestedDocumentReader(chunks_by_document)
    use_case = SearchEvidence(
        generate_embedding=GenerateChunkEmbedding(
            embedding_service=embedding_service
        ),
        vector_repository=vector_repository,
        ingested_document_reader=reader,
    )
    return use_case, embedding_service, vector_repository, reader


@pytest.mark.anyio
async def test_search_evidence_returns_chunks_with_text_and_source() -> None:
    document_id = uuid4()
    first_chunk_id = uuid4()
    second_chunk_id = uuid4()
    chunks = [
        ChunkRecord(
            id=first_chunk_id,
            document_id=document_id,
            text="A startup usa IA generativa para atendimento.",
            source_url="https://startup.example.com",
        ),
        ChunkRecord(
            id=second_chunk_id,
            document_id=document_id,
            text="A empresa menciona inferencia em producao.",
            source_url="https://startup.example.com",
        ),
    ]
    vector_results = [
        ChunkSearchResult(
            chunk_id=second_chunk_id,
            document_id=document_id,
            source_url="https://startup.example.com",
            score=0.87,
        )
    ]
    use_case, embedding_service, vector_repository, reader = _make_use_case(
        vector_results=vector_results,
        chunks_by_document={document_id: chunks},
    )

    view = await use_case.execute(
        SearchEvidenceInput(query="Como a startup usa IA?", limit=3)
    )

    assert view.query == "Como a startup usa IA?"
    assert len(view.results) == 1
    assert view.results[0].chunk_id == second_chunk_id
    assert view.results[0].text == "A empresa menciona inferencia em producao."
    assert view.results[0].score == 0.87
    assert embedding_service.inputs[0].text == "Como a startup usa IA?"
    assert vector_repository.searched_vectors == [(0.1, 0.2, 0.3)]
    assert vector_repository.limits == [3]
    assert reader.calls == [document_id]


@pytest.mark.anyio
async def test_search_evidence_reuses_document_chunks_for_multiple_results() -> None:
    document_id = uuid4()
    first_chunk_id = uuid4()
    second_chunk_id = uuid4()
    use_case, _, _, reader = _make_use_case(
        vector_results=[
            ChunkSearchResult(
                chunk_id=first_chunk_id,
                document_id=document_id,
                source_url="https://source.example.com",
                score=0.9,
            ),
            ChunkSearchResult(
                chunk_id=second_chunk_id,
                document_id=document_id,
                source_url="https://source.example.com",
                score=0.8,
            ),
        ],
        chunks_by_document={
            document_id: [
                ChunkRecord(
                    id=first_chunk_id,
                    document_id=document_id,
                    text="primeiro chunk relevante",
                    source_url="https://source.example.com",
                ),
                ChunkRecord(
                    id=second_chunk_id,
                    document_id=document_id,
                    text="segundo chunk relevante",
                    source_url="https://source.example.com",
                ),
            ]
        },
    )

    view = await use_case.execute(SearchEvidenceInput(query="pergunta"))

    assert len(view.results) == 2
    assert reader.calls == [document_id]


@pytest.mark.anyio
async def test_search_evidence_skips_stale_vector_without_chunk() -> None:
    document_id = uuid4()
    use_case, _, _, _ = _make_use_case(
        vector_results=[
            ChunkSearchResult(
                chunk_id=uuid4(),
                document_id=document_id,
                source_url="https://source.example.com",
                score=0.9,
            )
        ],
        chunks_by_document={document_id: []},
    )

    view = await use_case.execute(SearchEvidenceInput(query="pergunta"))

    assert view.results == []


@pytest.mark.anyio
async def test_search_evidence_rejects_empty_query() -> None:
    use_case, _, _, _ = _make_use_case(vector_results=[], chunks_by_document={})

    with pytest.raises(EmptyRagQueryError):
        await use_case.execute(SearchEvidenceInput(query="   "))
