"""Composicao das dependencias concretas do modulo agents.

Assim como ``ScrapingFactory``, este e o unico lugar do modulo ``agents`` que
conhece tipos concretos (hoje, o adaptador Gemini). Outros modulos nunca
instanciam ``GeminiEvidenceValidator`` diretamente — eles recebem o contrato
publico ``EvidenceValidationService`` atraves desta factory.
"""

from apps.api.src.config.settings import get_settings
from apps.api.src.modules.agents.application.public.semantic_investigator import (
    EvidenceValidationService,
)
from apps.api.src.modules.agents.graphs.evidence_validation.graph import (
    EvidenceValidationGraph,
)
from apps.api.src.modules.agents.infrastructure.llm.langchain_gemini_evidence_judge import (
    LangChainGeminiEvidenceJudge,
)


class AgentsFactory:
    """Ponto de composicao do modulo agents."""

    @staticmethod
    def create_evidence_validation_service() -> EvidenceValidationService | None:
        """Cria o servico publico de validacao de evidencias.

        Devolve ``None`` quando o Gemini nao esta configurado, da mesma forma
        que ``ScrapingFactory.create_pipeline`` faz para o
        ``semantic_validator`` da v7. Isso permite que o sistema continue
        funcionando (sem investigacao por agente) em ambientes sem a chave de
        API configurada.
        """

        settings = get_settings()

        if not settings.gemini_api_key:
            return None

        # V2: o servico publico agora e um grafo LangGraph. O Gemini fica
        # escondido atras de um avaliador LangChain, e o scraping continua
        # chamando o mesmo contrato ``EvidenceValidationService``.
        evidence_judge = LangChainGeminiEvidenceJudge(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

        return EvidenceValidationGraph(evidence_judge=evidence_judge)
