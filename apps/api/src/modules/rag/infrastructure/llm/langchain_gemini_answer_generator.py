"""Gerador de respostas RAG via LangChain + Gemini."""

from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apps.api.src.modules.rag.application.dto import (
    GenerateRagAnswerInput,
    RagAnswerView,
    RagCitationView,
)
from apps.api.src.modules.rag.application.public.answer_generator import (
    RagAnswerGenerator,
)
from apps.api.src.modules.rag.domain.exceptions import RagAnswerGenerationError


class GeminiRagCitationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    quote: str = Field(min_length=1, max_length=1000)


class GeminiRagAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=4000)
    citations: list[GeminiRagCitationResponse] = Field(min_length=1, max_length=10)


class LangChainGeminiRagAnswerGenerator(RagAnswerGenerator):
    """Gera respostas fundamentadas usando apenas evidencias recuperadas."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        temperature: float = 0.0,
        max_evidence_characters: int = 12_000,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY e obrigatoria.")
        if not model:
            raise ValueError("GEMINI_MODEL e obrigatorio.")

        self.max_evidence_characters = max_evidence_characters
        chat_model = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )
        self.structured_model = chat_model.with_structured_output(
            GeminiRagAnswerResponse
        )

    async def generate(self, answer_input: GenerateRagAnswerInput) -> RagAnswerView:
        messages = self._build_messages(answer_input)

        try:
            parsed = await self.structured_model.ainvoke(messages)
        except (ValidationError, ValueError, TypeError) as error:
            raise RagAnswerGenerationError(
                "Gemini devolveu uma resposta RAG invalida."
            ) from error
        except Exception as error:
            raise RagAnswerGenerationError(
                f"Gemini nao conseguiu gerar a resposta RAG: {error}."
            ) from error

        if not isinstance(parsed, GeminiRagAnswerResponse):
            raise RagAnswerGenerationError(
                "Gemini devolveu uma resposta RAG em formato inesperado."
            )

        return self._to_view(answer_input, parsed)

    def _build_messages(
        self, answer_input: GenerateRagAnswerInput
    ) -> list[SystemMessage | HumanMessage]:
        evidence_text = self._format_evidences(answer_input)
        system_message = SystemMessage(
            content=(
                "Voce e o modulo RAG do AI Venture Radar. Responda somente com "
                "base nas evidencias fornecidas. Nao invente fatos. Se as "
                "evidencias forem insuficientes, diga isso claramente. Sempre "
                "cite pelo menos um chunk_id usado."
            )
        )
        human_message = HumanMessage(
            content=(
                f"Pergunta:\n{answer_input.query}\n\n"
                "Evidencias recuperadas:\n"
                f"{evidence_text}\n\n"
                "Gere uma resposta curta, fundamentada, e uma lista de citacoes "
                "usando apenas chunk_id existentes nas evidencias."
            )
        )
        return [system_message, human_message]

    def _format_evidences(self, answer_input: GenerateRagAnswerInput) -> str:
        blocks: list[str] = []
        remaining = self.max_evidence_characters
        for index, evidence in enumerate(answer_input.evidences, start=1):
            text = evidence.text[:remaining]
            if not text:
                break
            block = (
                f"[{index}]\n"
                f"chunk_id: {evidence.chunk_id}\n"
                f"document_id: {evidence.document_id}\n"
                f"source_url: {evidence.source_url}\n"
                f"score: {evidence.score}\n"
                f"text: {text}\n"
            )
            blocks.append(block)
            remaining -= len(text)
            if remaining <= 0:
                break
        return "\n".join(blocks)

    def _to_view(
        self,
        answer_input: GenerateRagAnswerInput,
        parsed: GeminiRagAnswerResponse,
    ) -> RagAnswerView:
        evidences_by_id = {
            str(evidence.chunk_id): evidence for evidence in answer_input.evidences
        }
        citations: list[RagCitationView] = []

        for citation in parsed.citations:
            evidence = evidences_by_id.get(citation.chunk_id)
            if evidence is None:
                raise RagAnswerGenerationError(
                    f"Resposta citou chunk inexistente: {citation.chunk_id}."
                )
            citations.append(
                RagCitationView(
                    chunk_id=UUID(citation.chunk_id),
                    document_id=evidence.document_id,
                    source_url=evidence.source_url,
                    quote=citation.quote.strip(),
                )
            )

        if not citations:
            raise RagAnswerGenerationError("Resposta RAG nao trouxe citacoes.")

        return RagAnswerView(
            query=answer_input.query,
            answer=parsed.answer.strip(),
            citations=citations,
            evidences=answer_input.evidences,
        )
