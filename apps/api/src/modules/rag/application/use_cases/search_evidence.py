"""Caso de uso para buscar evidencias com busca hibrida + reranking."""

from apps.api.src.modules.embeddings.application.public.vector_repository import (
    VectorRepository,
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
from apps.api.src.modules.rag.application.ports import (
    EmbeddingGenerator,
    LexicalSearchRepository,
    Reranker,
)
from apps.api.src.modules.rag.application.public.retriever import Retriever
from apps.api.src.modules.rag.domain.exceptions import EmptyRagQueryError
from apps.api.src.modules.rag.domain.policies import RankedChunk, fuse_rankings

MIN_CANDIDATE_POOL = 20
CANDIDATE_POOL_MULTIPLIER = 4


class SearchEvidence(Retriever):
    """Busca hibrida (vetorial + lexical) com fusao RRF e reranking opcional.

    Fluxo (RAG V3 + V4): busca um pool de candidatos vetoriais (Qdrant) e
    lexicais (Postgres full-text) maior que o limite final -> funde via
    RRF (`domain/policies.py::fuse_rankings`) -> carrega o texto completo
    dos chunks fundidos via `ingestion` -> reranking (Cohere) se
    configurado, senao corta para o limite direto.
    """

    def __init__(
        self,
        *,
        embedding_generator: EmbeddingGenerator,
        vector_repository: VectorRepository,
        lexical_repository: LexicalSearchRepository,
        ingested_document_reader: IngestedDocumentReader,
        reranker: Reranker | None = None,
    ) -> None:
        self._embedding_generator = embedding_generator
        self._vector_repository = vector_repository
        self._lexical_repository = lexical_repository
        self._ingested_document_reader = ingested_document_reader
        self._reranker = reranker

    async def search(self, search_input: SearchEvidenceInput) -> SearchEvidenceView:
        query = search_input.query.strip()
        if not query:
            raise EmptyRagQueryError("Consulta RAG nao pode ser vazia.")

        limit = max(1, search_input.limit)
        candidate_limit = max(limit * CANDIDATE_POOL_MULTIPLIER, MIN_CANDIDATE_POOL)

        embedding_vector = await self._embedding_generator.generate(query)
        vector_results = await self._vector_repository.search(
            embedding_vector,
            limit=candidate_limit,
            source_type=search_input.source_type,
        )
        lexical_results = await self._lexical_repository.search(
            query,
            limit=candidate_limit,
            source_type=search_input.source_type,
        )

        fused = fuse_rankings(
            ranked_lists=[
                [
                    RankedChunk(chunk_id=item.chunk_id, document_id=item.document_id)
                    for item in vector_results
                ],
                [
                    RankedChunk(chunk_id=item.chunk_id, document_id=item.document_id)
                    for item in lexical_results
                ],
            ],
            limit=candidate_limit,
        )

        source_urls = {item.chunk_id: item.source_url for item in vector_results}
        chunks_by_document: dict = {}
        evidence_chunks: list[EvidenceChunkView] = []

        for item in fused:
            if item.document_id not in chunks_by_document:
                chunks_by_document[item.document_id] = {
                    chunk.id: chunk
                    for chunk in await self._ingested_document_reader.list_chunks_by_document_id(
                        item.document_id
                    )
                }

            chunk: ChunkRecord | None = chunks_by_document[item.document_id].get(
                item.chunk_id
            )
            if chunk is None:
                # Chunk "stale" (presente no indice vetorial/lexical mas
                # ja removido da ingestion).
                continue

            evidence_chunks.append(
                EvidenceChunkView(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    source_url=source_urls.get(item.chunk_id) or chunk.source_url,
                    source_type=chunk.source_type.value,
                    text=chunk.text,
                    score=item.score,
                )
            )

        if self._reranker is not None:
            evidence_chunks = await self._reranker.rerank(
                query, evidence_chunks, top_n=limit
            )
        else:
            evidence_chunks = evidence_chunks[:limit]

        return SearchEvidenceView(query=query, results=evidence_chunks)

    async def execute(self, search_input: SearchEvidenceInput) -> SearchEvidenceView:
        """Alias para manter o padrao dos outros casos de uso."""

        return await self.search(search_input)
