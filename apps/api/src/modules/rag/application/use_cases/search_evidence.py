"""Caso de uso para buscar evidencias semanticamente."""

from uuid import uuid4

from apps.api.src.modules.embeddings.application.dto import GenerateChunkEmbeddingInput
from apps.api.src.modules.embeddings.application.public.vector_repository import (
    VectorRepository,
)
from apps.api.src.modules.embeddings.application.use_cases.generate_chunk_embedding import (
    GenerateChunkEmbedding,
)
from apps.api.src.modules.ingestion.application.public.ingested_reader import (
    ChunkRecord,
    IngestedDocumentReader,
)
from apps.api.src.modules.rag.application.dto import (
    EvidenceChunkView,
    SearchEvidenceInput,
    SearchEvidenceView,
)
from apps.api.src.modules.rag.application.public.retriever import Retriever
from apps.api.src.modules.rag.domain.exceptions import EmptyRagQueryError


class SearchEvidence(Retriever):
    """Busca chunks relevantes usando embedding da pergunta + Qdrant."""

    def __init__(
        self,
        *,
        generate_embedding: GenerateChunkEmbedding,
        vector_repository: VectorRepository,
        ingested_document_reader: IngestedDocumentReader,
    ) -> None:
        self._generate_embedding = generate_embedding
        self._vector_repository = vector_repository
        self._ingested_document_reader = ingested_document_reader

    async def search(self, search_input: SearchEvidenceInput) -> SearchEvidenceView:
        query = search_input.query.strip()
        if not query:
            raise EmptyRagQueryError("Consulta RAG nao pode ser vazia.")

        limit = max(1, search_input.limit)
        embedding = await self._generate_embedding.execute(
            GenerateChunkEmbeddingInput(chunk_id=uuid4(), text=query)
        )
        vector_results = await self._vector_repository.search(
            embedding.values,
            limit=limit,
        )

        chunks_by_document: dict = {}
        evidence_chunks: list[EvidenceChunkView] = []

        for result in vector_results:
            if result.document_id not in chunks_by_document:
                chunks_by_document[result.document_id] = {
                    chunk.id: chunk
                    for chunk in await self._ingested_document_reader.list_chunks_by_document_id(
                        result.document_id
                    )
                }

            chunk: ChunkRecord | None = chunks_by_document[result.document_id].get(
                result.chunk_id
            )
            if chunk is None:
                continue

            evidence_chunks.append(
                EvidenceChunkView(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    source_url=result.source_url or chunk.source_url,
                    text=chunk.text,
                    score=result.score,
                )
            )

        return SearchEvidenceView(query=query, results=evidence_chunks)

    async def execute(self, search_input: SearchEvidenceInput) -> SearchEvidenceView:
        """Alias para manter o padrao dos outros casos de uso."""

        return await self.search(search_input)
