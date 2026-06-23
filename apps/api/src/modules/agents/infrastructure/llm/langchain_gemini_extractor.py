"""Extrator Gemini via LangChain para o Extraction Agent.

Recebe o perfil/evidencias da startup, chama o modelo Gemini e devolve um
``ExtractionResult`` validado. Nao sabe nada sobre LangGraph — o grafo
fica em ``graphs/extraction`` e usa este extrator como uma ferramenta de
extracao estruturada.
"""

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from apps.api.src.shared.observability import get_langfuse_callbacks

from apps.api.src.modules.agents.application.dto import (
    ExtractionInput,
    ExtractionResult,
)
from apps.api.src.modules.agents.application.public.extractor import (
    ExtractionService,
)
from apps.api.src.modules.agents.domain.enums import ExtractedFundingStage
from apps.api.src.modules.agents.domain.exceptions import AgentExtractionError


class LangChainGeminiExtractionResponse(BaseModel):
    """Schema que a LLM deve obedecer."""

    model_config = ConfigDict(extra="forbid")

    founders: list[str] = Field(default_factory=list, max_length=20)
    funding_stage: ExtractedFundingStage
    funding_amount_usd: float | None = None
    customers: list[str] = Field(default_factory=list, max_length=20)
    sector: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)


class LangChainGeminiExtractor(ExtractionService):
    """Servico que usa Gemini, via LangChain, para extrair dados estruturados."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        temperature: float = 0.0,
        max_evidence_characters: int = 20_000,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY e obrigatoria.")
        if not model:
            raise ValueError("GEMINI_MODEL e obrigatorio.")

        self.model = model
        self.max_evidence_characters = max_evidence_characters

        chat_model = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )
        self.structured_model = chat_model.with_structured_output(
            LangChainGeminiExtractionResponse
        )

    async def extract(
        self,
        extraction_input: ExtractionInput,
    ) -> ExtractionResult:
        """Chama Gemini via LangChain e converte a saida para o DTO publico."""

        messages = self._build_messages(extraction_input)

        try:
            parsed = await self.structured_model.ainvoke(
                messages, config={"callbacks": get_langfuse_callbacks()}
            )
        except (ValidationError, ValueError, TypeError) as error:
            raise AgentExtractionError(
                "Gemini devolveu uma resposta de extracao invalida."
            ) from error
        except Exception as error:
            raise AgentExtractionError(
                f"Gemini nao conseguiu concluir a extracao: {error}."
            ) from error

        if not isinstance(parsed, LangChainGeminiExtractionResponse):
            raise AgentExtractionError(
                "Gemini devolveu uma resposta de extracao em formato inesperado."
            )

        return ExtractionResult(
            founders=parsed.founders,
            funding_stage=parsed.funding_stage,
            funding_amount_usd=parsed.funding_amount_usd,
            customers=parsed.customers,
            sector=parsed.sector,
            description=parsed.description,
        )

    def _build_messages(
        self,
        extraction_input: ExtractionInput,
    ) -> list[SystemMessage | HumanMessage]:
        """Monta as mensagens enviadas ao Gemini."""

        evidence_block = "\n".join(
            f"- {text[: self.max_evidence_characters]}"
            for text in extraction_input.evidence_texts
        ) or "(nenhuma evidencia textual disponivel)"

        system_message = SystemMessage(
            content=(
                "Voce e o Extraction Agent do AI Venture Radar. Sua tarefa e "
                "extrair fatos estruturados (founders, estagio de funding, "
                "valor de funding em USD, clientes) APENAS quando explicitamente "
                "mencionados nas evidencias. Nunca infira, deduza ou invente um "
                "dado que nao esteja escrito no texto. Quando um dado nao for "
                "mencionado, devolva lista vazia (founders/customers), "
                "'unknown' (funding_stage) ou null (funding_amount_usd) — nao "
                "tente adivinhar.\n\n"
                "Alem disso, escreva 'sector' (rotulo curto de categoria, ex. "
                "'Data Analytics', 'Healthcare AI', 'DevTools') e 'description' "
                "(1-2 frases resumindo o produto). Os dois campos SEMPRE em "
                "ingles, mesmo que as evidencias estejam em outro idioma — isso "
                "e so para casar com o vocabulario do catalogo de tecnologias "
                "NVIDIA, nao e traducao do texto original. Baseie-se somente no "
                "que as evidencias realmente descrevem; se nao houver sinal "
                "suficiente para um resumo confiavel, devolva null em vez de "
                "generico ou inventado."
            )
        )

        human_message = HumanMessage(
            content=(
                "Extraia os dados estruturados desta startup a partir das "
                "evidencias abaixo.\n\n"
                f"Nome: {extraction_input.name}\n"
                f"Setor: {extraction_input.sector or 'desconhecido'}\n"
                f"Descricao: {extraction_input.description or 'ausente'}\n\n"
                "--- Evidencias coletadas ---\n"
                f"{evidence_block}"
            )
        )

        return [system_message, human_message]
