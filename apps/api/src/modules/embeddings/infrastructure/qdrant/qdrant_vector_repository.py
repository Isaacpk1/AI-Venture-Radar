"""Persistencia e busca vetorial no Qdrant.

Implementacao V3 do contrato publico ``VectorRepository``. A colecao e'
criada de forma idempotente no primeiro upsert, usando a dimensao do vetor
inserido — ainda nao ha gestao antecipada de schema porque nenhum vetor
real foi persistido antes desta versao.
"""

from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from apps.api.src.modules.embeddings.application.dto import (
    ChunkEmbeddingRecord,
    ChunkSearchResult,
)
from apps.api.src.modules.embeddings.application.public.vector_repository import (
    VectorRepository,
)
from apps.api.src.modules.embeddings.domain.exceptions import (
    EmbeddingCollectionSchemaMismatchError,
)


class QdrantVectorRepository(VectorRepository):
    """Persiste e busca vetores de chunks em uma colecao do Qdrant."""

    def __init__(self, *, url: str, collection_name: str) -> None:
        self._client = AsyncQdrantClient(url=url)
        self._collection_name = collection_name

    async def upsert(self, record: ChunkEmbeddingRecord) -> None:
        await self._ensure_collection(record.dimension, record.model_name)
        await self._client.upsert(
            collection_name=self._collection_name,
            points=[
                PointStruct(
                    id=str(record.chunk_id),
                    vector=list(record.values),
                    payload={
                        "document_id": str(record.document_id),
                        "source_url": record.source_url,
                        "source_type": record.source_type,
                        "model_name": record.model_name,
                    },
                )
            ],
        )

    async def search(
        self,
        query_vector: tuple[float, ...],
        *,
        limit: int = 5,
        source_type: str | None = None,
    ) -> list[ChunkSearchResult]:
        response = await self._client.query_points(
            collection_name=self._collection_name,
            query=list(query_vector),
            query_filter=self._build_filter(source_type),
            limit=limit,
        )
        return [
            ChunkSearchResult(
                chunk_id=UUID(str(point.id)),
                document_id=UUID(point.payload["document_id"]),
                source_url=point.payload["source_url"],
                source_type=point.payload.get("source_type", "startup_evidence"),
                score=point.score,
            )
            for point in response.points
        ]

    async def get_by_chunk_id(self, chunk_id: UUID) -> ChunkEmbeddingRecord | None:
        if not await self._client.collection_exists(self._collection_name):
            return None

        points = await self._client.retrieve(
            collection_name=self._collection_name,
            ids=[str(chunk_id)],
            with_vectors=True,
        )
        if not points:
            return None

        point = points[0]
        values = tuple(point.vector)
        return ChunkEmbeddingRecord(
            chunk_id=chunk_id,
            document_id=UUID(point.payload["document_id"]),
            source_url=point.payload["source_url"],
            source_type=point.payload.get("source_type", "startup_evidence"),
            values=values,
            dimension=len(values),
            model_name=point.payload["model_name"],
        )

    def _build_filter(self, source_type: str | None) -> Filter | None:
        if source_type is None:
            return None
        return Filter(
            must=[
                FieldCondition(
                    key="source_type",
                    match=MatchValue(value=source_type),
                )
            ]
        )

    async def _ensure_collection(self, dimension: int, model_name: str) -> None:
        if not await self._client.collection_exists(self._collection_name):
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
                metadata={
                    "embedding_dimension": dimension,
                    "embedding_model_name": model_name,
                },
            )
            return

        collection = await self._client.get_collection(self._collection_name)
        vectors = collection.config.params.vectors
        collection_dimension = getattr(vectors, "size", None)
        metadata = collection.config.metadata or {}
        collection_model_name = metadata.get("embedding_model_name")

        if collection_dimension != dimension:
            raise EmbeddingCollectionSchemaMismatchError(
                "A colecao Qdrant usa dimensao "
                f"{collection_dimension}, mas o modelo {model_name!r} gerou "
                f"dimensao {dimension}. Crie ou reindexe uma colecao compativel."
            )
        if collection_model_name is None:
            raise EmbeddingCollectionSchemaMismatchError(
                "A colecao Qdrant existente nao declara o modelo de embedding. "
                "Reindexe os vetores em uma colecao com metadata de schema antes "
                "de continuar a gravar."
            )
        if collection_model_name != model_name:
            raise EmbeddingCollectionSchemaMismatchError(
                "A colecao Qdrant usa o modelo "
                f"{collection_model_name!r}, mas a escrita usa {model_name!r}. "
                "Crie ou reindexe uma colecao compativel."
            )
