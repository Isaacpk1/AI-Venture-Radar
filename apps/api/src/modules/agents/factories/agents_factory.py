"""Composicao das dependencias concretas do modulo agents.

Assim como ``ScrapingFactory``, este e o unico lugar do modulo ``agents`` que
conhece tipos concretos (hoje, o adaptador Gemini). Outros modulos nunca
instanciam ``GeminiEvidenceValidator`` diretamente — eles recebem o contrato
publico ``EvidenceValidationService`` atraves desta factory.
"""

from apps.api.src.config.settings import get_settings
from apps.api.src.modules.agents.application.ports import AgentTaskDispatcher
from apps.api.src.modules.agents.application.public.semantic_investigator import (
    EvidenceValidationService,
)
from apps.api.src.modules.agents.application.public.search_planner import (
    SearchPlanningService,
)
from apps.api.src.modules.agents.application.use_cases.execute_agent_job import (
    ExecuteAgentJob,
)
from apps.api.src.modules.agents.graphs.evidence_validation.graph import (
    EvidenceValidationGraph,
)
from apps.api.src.modules.agents.graphs.search_planning.graph import (
    SearchPlanningGraph,
)
from apps.api.src.modules.agents.infrastructure.llm.langchain_gemini_evidence_judge import (
    LangChainGeminiEvidenceJudge,
)
from apps.api.src.modules.agents.infrastructure.llm.langchain_gemini_search_planner import (
    LangChainGeminiSearchPlanner,
)
from apps.api.src.modules.agents.infrastructure.queue.dramatiq_agent_dispatcher import (
    DramatiqAgentJobPublisher,
    DramatiqAgentTaskDispatcher,
)
from apps.api.src.shared.queue.dramatiq_broker import broker


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

    @staticmethod
    def create_search_planning_service() -> SearchPlanningService | None:
        """Cria o servico publico do Search Planner Agent.

        Assim como a validacao de evidencias, este agente depende de Gemini.
        Sem chave configurada, devolvemos ``None`` para evitar custo acidental e
        permitir que o sistema suba em ambientes locais.
        """

        settings = get_settings()

        if not settings.gemini_api_key:
            return None

        planner = LangChainGeminiSearchPlanner(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

        return SearchPlanningGraph(planner=planner)

    @staticmethod
    def create_agent_task_dispatcher() -> AgentTaskDispatcher:
        """Cria dispatcher para publicar execucoes na fila ``agents``."""

        return DramatiqAgentTaskDispatcher(
            DramatiqAgentJobPublisher(broker),
        )

    @staticmethod
    def create_execute_agent_job() -> ExecuteAgentJob:
        """Cria o caso de uso chamado pelo agent_worker."""

        return ExecuteAgentJob()
