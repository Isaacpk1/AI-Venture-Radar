"""Composicao das dependencias concretas do modulo embeddings."""

from apps.api.src.config.settings import get_settings
from apps.api.src.modules.embeddings.application.public.embedding_service import (
    EmbeddingService,
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
from apps.api.src.modules.embeddings.infrastructure.gemini.gemini_embedding_provider import (
    GeminiEmbeddingProvider,
)
from apps.api.src.modules.embeddings.infrastructure.qdrant.qdrant_vector_repository import (
    QdrantVectorRepository,
)


class EmbeddingsFactory:
    """Ponto de composicao do modulo embeddings."""

    @staticmethod
    def create_embedding_service() -> EmbeddingService | None:
        """Cria o provider real de embeddings.

        Devolve ``None`` quando ``GEMINI_API_KEY`` nao esta configurada — sem
        fallback silencioso para o provider fake, que so existe para testes
        (``infrastructure/fake/deterministic_fake_provider.py``). A falta de
        servico e' tratada na hora do uso real, em
        ``GenerateChunkEmbedding.execute()``.
        """

        settings = get_settings()
        if not settings.gemini_api_key:
            return None

        return GeminiEmbeddingProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_embedding_model,
        )

    @staticmethod
    def create_generate_chunk_embedding() -> GenerateChunkEmbedding:
        """Cria o caso de uso pronto para gerar embeddings de chunks."""

        return GenerateChunkEmbedding(
            embedding_service=EmbeddingsFactory.create_embedding_service(),
        )

    @staticmethod
    def create_vector_repository() -> VectorRepository:
        """Cria o repositorio de vetores (Qdrant)."""

        settings = get_settings()
        return QdrantVectorRepository(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection_name,
        )

    @staticmethod
    def create_upsert_chunk_embedding() -> UpsertChunkEmbedding:
        """Cria o caso de uso pronto para gerar e persistir embeddings de chunks."""

        return UpsertChunkEmbedding(
            generate_chunk_embedding=EmbeddingsFactory.create_generate_chunk_embedding(),
            vector_repository=EmbeddingsFactory.create_vector_repository(),
        )
