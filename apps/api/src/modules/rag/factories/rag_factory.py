"""Composicao das dependencias concretas do modulo RAG."""

from apps.api.src.config.settings import get_settings
from apps.api.src.modules.embeddings.factories.embeddings_factory import (
    EmbeddingsFactory,
)
from apps.api.src.modules.ingestion.factories.ingestion_factory import IngestionFactory
from apps.api.src.modules.rag.application.ports import LexicalSearchRepository, Reranker
from apps.api.src.modules.rag.application.public.answer_generator import (
    RagAnswerGenerator,
)
from apps.api.src.modules.rag.application.use_cases.answer_question import (
    AnswerQuestion,
)
from apps.api.src.modules.rag.application.use_cases.search_evidence import (
    SearchEvidence,
)
from apps.api.src.modules.rag.infrastructure.database.postgres_lexical_search_repository import (
    PostgresLexicalSearchRepository,
)
from apps.api.src.modules.rag.infrastructure.llm.langchain_gemini_answer_generator import (
    LangChainGeminiRagAnswerGenerator,
)
from apps.api.src.modules.rag.infrastructure.reranking.cohere_reranker import (
    CohereReranker,
)


class RagFactory:
    """Ponto de composicao do modulo RAG."""

    @staticmethod
    def create_lexical_search_repository() -> LexicalSearchRepository:
        """Busca lexical (Postgres full-text) - sempre disponivel, sem API key."""

        return PostgresLexicalSearchRepository()

    @staticmethod
    def create_reranker() -> Reranker | None:
        """Cria o reranker Cohere, quando configurado (RAG V4)."""

        settings = get_settings()
        if not settings.cohere_api_key:
            return None

        return CohereReranker(api_key=settings.cohere_api_key)

    @staticmethod
    def create_search_evidence() -> SearchEvidence:
        return SearchEvidence(
            generate_embedding=EmbeddingsFactory.create_generate_chunk_embedding(),
            vector_repository=EmbeddingsFactory.create_vector_repository(),
            lexical_repository=RagFactory.create_lexical_search_repository(),
            ingested_document_reader=IngestionFactory.create_ingested_document_reader(),
            reranker=RagFactory.create_reranker(),
        )

    @staticmethod
    def create_answer_generator() -> RagAnswerGenerator | None:
        """Cria o gerador de resposta RAG via Gemini, quando configurado."""

        settings = get_settings()
        if not settings.gemini_api_key:
            return None

        return LangChainGeminiRagAnswerGenerator(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

    @staticmethod
    def create_answer_question() -> AnswerQuestion:
        return AnswerQuestion(
            search_evidence=RagFactory.create_search_evidence(),
            answer_generator=RagFactory.create_answer_generator(),
        )
