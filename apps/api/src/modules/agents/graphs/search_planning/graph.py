"""Grafo LangGraph do Search Planner Agent.

A V3 cria um agente novo: ele transforma um caso de `needs_more_sources` em um
plano de queries. Ele ainda nao executa scraping; isso fica para a V4.
"""

from langgraph.graph import END, StateGraph

from apps.api.src.modules.agents.application.dto import (
    SearchPlanInput,
    SearchPlanResult,
)
from apps.api.src.modules.agents.application.public.search_planner import (
    SearchPlanningService,
)
from apps.api.src.modules.agents.graphs.search_planning.state import (
    SearchPlanningState,
)


class SearchPlanningGraph(SearchPlanningService):
    """Orquestra a geracao de plano de busca usando LangGraph."""

    def __init__(self, *, planner: SearchPlanningService) -> None:
        self.planner = planner
        self.model = getattr(planner, "model", None)
        self.graph = self._compile_graph()

    async def plan_searches(self, plan_input: SearchPlanInput) -> SearchPlanResult:
        """Executa o grafo e devolve o plano publico."""

        final_state = await self.graph.ainvoke({"plan_input": plan_input})
        return final_state["result"]

    def _compile_graph(self):
        """Define o fluxo da V3.

        A sequencia atual e simples:

        prepare_context -> generate_plan -> finalize

        Nas proximas versoes, este grafo pode ganhar nodes para deduplicar
        fontes, consultar historico e escolher provedores de busca.
        """

        workflow = StateGraph(SearchPlanningState)

        workflow.add_node("prepare_context", self._prepare_context)
        workflow.add_node("generate_plan", self._generate_plan)
        workflow.add_node("finalize", self._finalize)

        workflow.set_entry_point("prepare_context")
        workflow.add_edge("prepare_context", "generate_plan")
        workflow.add_edge("generate_plan", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _prepare_context(
        self,
        state: SearchPlanningState,
    ) -> SearchPlanningState:
        """Prepara um resumo interno do caso."""

        plan_input = state["plan_input"]
        prepared_context = (
            f"startup={plan_input.startup_name or 'unknown'}; "
            f"source_url={plan_input.source_url}; "
            f"max_queries={plan_input.max_queries}; "
            f"known_terms={len(plan_input.known_terms)}"
        )

        return {"prepared_context": prepared_context}

    async def _generate_plan(
        self,
        state: SearchPlanningState,
    ) -> SearchPlanningState:
        """Chama o planejador configurado para gerar queries."""

        plan = await self.planner.plan_searches(state["plan_input"])
        return {"llm_plan": plan}

    async def _finalize(
        self,
        state: SearchPlanningState,
    ) -> SearchPlanningState:
        """Define a saida final do grafo."""

        return {"result": state["llm_plan"]}
