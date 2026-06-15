"""Grafo LangGraph do Evidence Validation Agent.

Esta e a V2 real do agente. O contrato publico continua sendo
``EvidenceValidationService``: quem chama o agente ainda usa
``await service.investigate(input)``. A diferenca e que, internamente, agora
existe um fluxo LangGraph com nodes pequenos e estado explicito.
"""

from langgraph.graph import END, StateGraph

from apps.api.src.modules.agents.application.dto import (
    EvidenceValidationInput,
    EvidenceValidationResult,
)
from apps.api.src.modules.agents.application.public.semantic_investigator import (
    EvidenceValidationService,
)
from apps.api.src.modules.agents.graphs.evidence_validation.state import (
    EvidenceValidationState,
)


class EvidenceValidationGraph(EvidenceValidationService):
    """Orquestra a validacao de evidencia usando LangGraph."""

    def __init__(self, *, evidence_judge: EvidenceValidationService) -> None:
        self.evidence_judge = evidence_judge
        # Mantemos ``model`` quando o avaliador interno expuser esse atributo.
        # Isso ajuda logs/testes de composicao sem vazar detalhes do grafo para
        # o contrato publico.
        self.model = getattr(evidence_judge, "model", None)
        self.graph = self._compile_graph()

    async def investigate(
        self,
        investigation_input: EvidenceValidationInput,
    ) -> EvidenceValidationResult:
        """Executa o grafo e devolve apenas o resultado publico."""

        final_state = await self.graph.ainvoke(
            {"investigation_input": investigation_input}
        )
        return final_state["result"]

    def _compile_graph(self):
        """Define os nodes e as transicoes do LangGraph.

        A V2 ainda e simples de proposito:

        prepare_context -> judge_evidence -> finalize

        Mesmo simples, isso ja cria a base para crescer. Nas proximas versoes,
        podemos adicionar roteadores condicionais, tools de busca e checkpoint.
        """

        workflow = StateGraph(EvidenceValidationState)

        workflow.add_node("prepare_context", self._prepare_context)
        workflow.add_node("judge_evidence", self._judge_evidence)
        workflow.add_node("finalize", self._finalize)

        workflow.set_entry_point("prepare_context")
        workflow.add_edge("prepare_context", "judge_evidence")
        workflow.add_edge("judge_evidence", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _prepare_context(
        self,
        state: EvidenceValidationState,
    ) -> EvidenceValidationState:
        """Prepara um resumo interno para auditoria e futuras decisoes.

        Hoje esse resumo ainda nao muda a decisao. Ele existe para deixar o
        estado do grafo explicito e abrir espaco para proximos nodes.
        """

        investigation_input = state["investigation_input"]
        prepared_context = (
            f"url={investigation_input.url}; "
            f"quality_score={investigation_input.quality_score}; "
            f"semantic_confidence={investigation_input.semantic_confidence}; "
            f"semantic_decision={investigation_input.semantic_decision}"
        )

        return {"prepared_context": prepared_context}

    async def _judge_evidence(
        self,
        state: EvidenceValidationState,
    ) -> EvidenceValidationState:
        """Chama o avaliador semantico configurado para produzir a decisao."""

        result = await self.evidence_judge.investigate(state["investigation_input"])
        return {"llm_result": result}

    async def _finalize(
        self,
        state: EvidenceValidationState,
    ) -> EvidenceValidationState:
        """Normaliza a saida final do grafo.

        Ter um node final separado evita espalhar detalhes de retorno pelos
        nodes anteriores. Quando adicionarmos mais etapas, este sera o ponto
        unico para montar a resposta publica.
        """

        return {"result": state["llm_result"]}
