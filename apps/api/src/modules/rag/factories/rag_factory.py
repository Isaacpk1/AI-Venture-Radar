"""Composicao das dependencias concretas do modulo RAG."""

from apps.api.src.config.settings import get_settings
from apps.api.src.modules.embeddings.factories.embeddings_factory import (
    EmbeddingsFactory,
)
from apps.api.src.modules.ingestion.factories.ingestion_factory import IngestionFactory
from apps.api.src.modules.rag.application.public.answer_generator import (
    RagAnswerGenerator,
)
from apps.api.src.modules.rag.application.use_cases.answer_question import (
    AnswerQuestion,
)
from apps.api.src.modules.rag.application.use_cases.search_evidence import (
    SearchEvidence,
)
from apps.api.src.modules.rag.infrastructure.llm.langchain_gemini_answer_generator import (
    LangChainGeminiRagAnswerGenerator,
)


class RagFactory:
    """Ponto de composicao do modulo RAG."""

    @staticmethod
    def create_search_evidence() -> SearchEvidence:
        return SearchEvidence(
            generate_embedding=EmbeddingsFactory.create_generate_chunk_embedding(),
            vector_repository=EmbeddingsFactory.create_vector_repository(),
            ingested_document_reader=IngestionFactory.create_ingested_document_reader(),
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
