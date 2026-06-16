"""Grafo LangGraph do Evidence Validation Agent (V6: checkpointer + interrupt).

A V6 adiciona suporte a checkpoint PostgreSQL e a retomada apos interrupcao.
O contrato publico ``EvidenceValidationService`` continua o mesmo; quem chama
ainda usa ``await service.investigate(input, thread_id=...)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph

from apps.api.src.modules.agents.application.dto import (
    EvidenceValidationInput,
    EvidenceValidationResult,
)
from apps.api.src.modules.agents.application.public.semantic_investigator import (
    EvidenceValidationService,
)
from apps.api.src.modules.agents.domain.exceptions import AgentRunInterruptedError
from apps.api.src.modules.agents.graphs.evidence_validation.state import (
    EvidenceValidationState,
)

if TYPE_CHECKING:
    from apps.api.src.modules.agents.infrastructure.checkpoints.postgres_checkpointer import (
        PostgresCheckpointer,
    )


class EvidenceValidationGraph(EvidenceValidationService):
    """Orquestra a validacao de evidencia usando LangGraph."""

    def __init__(
        self,
        *,
        evidence_judge: EvidenceValidationService,
        checkpointer: "PostgresCheckpointer | None" = None,
    ) -> None:
        self.evidence_judge = evidence_judge
        self.model = getattr(evidence_judge, "model", None)
        self._checkpointer = checkpointer
        self._workflow = self._build_workflow()
        # Grafo pre-compilado sem checkpoint para chamadas sem thread_id.
        self._graph_no_cp = self._workflow.compile()
        # Grafo com checkpoint (criado na primeira invocacao com thread_id).
        self._graph_with_cp: Any = None

    async def investigate(
        self,
        investigation_input: EvidenceValidationInput,
        *,
        thread_id: str | None = None,
    ) -> EvidenceValidationResult:
        """Executa o grafo e devolve apenas o resultado publico."""

        graph, config = await self._resolve_graph_and_config(thread_id)
        try:
            final_state = await graph.ainvoke(
                {"investigation_input": investigation_input},
                config=config,
            )
        except Exception as exc:
            if type(exc).__name__ == "GraphInterrupt":
                interrupt_value = repr(exc.args[0]) if exc.args else "interrupt"
                raise AgentRunInterruptedError(interrupt_value) from exc
            raise

        return final_state["result"]

    async def resume(
        self,
        thread_id: str,
        resume_value: object,
    ) -> EvidenceValidationResult:
        """Retoma uma investigacao pausada a partir do checkpoint salvo."""

        from langgraph.types import Command

        graph, config = await self._resolve_graph_and_config(thread_id)
        try:
            final_state = await graph.ainvoke(Command(resume=resume_value), config=config)
        except Exception as exc:
            if type(exc).__name__ == "GraphInterrupt":
                interrupt_value = repr(exc.args[0]) if exc.args else "interrupt"
                raise AgentRunInterruptedError(interrupt_value) from exc
            raise

        return final_state["result"]

    async def _resolve_graph_and_config(
        self, thread_id: str | None
    ) -> tuple[Any, dict]:
        if thread_id and self._checkpointer is not None:
            if self._graph_with_cp is None:
                saver = await self._checkpointer.get_saver()
                self._graph_with_cp = self._workflow.compile(checkpointer=saver)
            return self._graph_with_cp, {"configurable": {"thread_id": thread_id}}
        return self._graph_no_cp, {}

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(EvidenceValidationState)

        workflow.add_node("prepare_context", self._prepare_context)
        workflow.add_node("judge_evidence", self._judge_evidence)
        workflow.add_node("finalize", self._finalize)

        workflow.set_entry_point("prepare_context")
        workflow.add_edge("prepare_context", "judge_evidence")
        workflow.add_edge("judge_evidence", "finalize")
        workflow.add_edge("finalize", END)

        return workflow

    async def _prepare_context(
        self,
        state: EvidenceValidationState,
    ) -> EvidenceValidationState:
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
        result = await self.evidence_judge.investigate(state["investigation_input"])
        return {"llm_result": result}

    async def _finalize(
        self,
        state: EvidenceValidationState,
    ) -> EvidenceValidationState:
        return {"result": state["llm_result"]}
