"""Composicao das dependencias concretas do modulo embeddings."""

from apps.api.src.modules.embeddings.application.public.embedding_service import (
    EmbeddingService,
)
from apps.api.src.modules.embeddings.application.use_cases.generate_chunk_embedding import (
    GenerateChunkEmbedding,
)
from apps.api.src.modules.embeddings.infrastructure.fake.deterministic_fake_provider import (
    DeterministicFakeEmbeddingProvider,
)


class EmbeddingsFactory:
    """Ponto de composicao do modulo embeddings."""

    @staticmethod
    def create_embedding_service() -> EmbeddingService:
        """Cria o provider de embeddings.

        V1: sempre devolve o provider fake deterministico. V2 trocara este
        metodo para escolher entre fake e um provider real, sem alterar
        ``create_generate_chunk_embedding`` nem o contrato publico.
        """

        return DeterministicFakeEmbeddingProvider()

    @staticmethod
    def create_generate_chunk_embedding() -> GenerateChunkEmbedding:
        """Cria o caso de uso pronto para gerar embeddings de chunks."""

        return GenerateChunkEmbedding(
            embedding_service=EmbeddingsFactory.create_embedding_service(),
        )
