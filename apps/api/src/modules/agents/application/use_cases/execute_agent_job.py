"""Caso de uso executado pelo agent_worker."""

from uuid import UUID

from apps.api.src.modules.agents.application.agent_run_payloads import (
    evidence_validation_input_from_payload,
    evidence_validation_result_to_payload,
    search_plan_input_from_payload,
    search_plan_result_to_payload,
)
from apps.api.src.modules.agents.application.public.search_planner import (
    SearchPlanningService,
)
from apps.api.src.modules.agents.application.public.semantic_investigator import (
    EvidenceValidationService,
)
from apps.api.src.modules.agents.application.unit_of_work import (
    AgentsUnitOfWorkFactory,
)
from apps.api.src.modules.agents.domain.entities import AgentStep
from apps.api.src.modules.agents.domain.enums import AgentType
from apps.api.src.modules.agents.domain.exceptions import (
    AgentRunNotFoundError,
    AgentServiceUnavailableError,
    UnsupportedAgentJobError,
)


class ExecuteAgentJob:
    """Executa uma tarefa de agente recebida pela fila.

    Recebe um ``run_id``, busca o ``AgentRun`` persistido no banco, reconstrói
    o DTO de entrada e despacha para o grafo correto com base em ``agent_type``.
    Falhas do LLM ou do grafo são capturadas e persistidas como status ``failed``.
    """

    def __init__(
        self,
        uow_factory: AgentsUnitOfWorkFactory,
        evidence_validation_service: EvidenceValidationService | None = None,
        search_planning_service: SearchPlanningService | None = None,
    ) -> None:
        self.uow_factory = uow_factory
        self.evidence_validation_service = evidence_validation_service
        self.search_planning_service = search_planning_service

    async def execute(self, *, run_id: UUID) -> None:
        async with self.uow_factory() as uow:
            run = await uow.run_repository.get_by_id(run_id)
            if run is None:
                raise AgentRunNotFoundError(f"AgentRun {run_id} nao encontrado.")

            run.start()
            step = AgentStep(
                run_id=run.id,
                name=f"execute_{run.agent_type.value}",
                input_payload={"agent_type": run.agent_type.value, "run_id": str(run_id)},
            )

            try:
                output_payload = await self._run_graph(run.agent_type, run.input_payload)
                step.complete(output_payload)
                run.complete(output_payload)
            except Exception as exc:
                reason = f"{type(exc).__name__}: {exc}"
                step.fail(reason)
                run.fail(reason)

            await uow.run_repository.save(run)
            await uow.step_repository.save(step)
            await uow.commit()

    async def _run_graph(
        self,
        agent_type: AgentType,
        input_payload: dict[str, object],
    ) -> dict[str, object]:
        if agent_type is AgentType.EVIDENCE_VALIDATION:
            if self.evidence_validation_service is None:
                raise AgentServiceUnavailableError(
                    "Evidence validation service nao configurado (verifique GEMINI_API_KEY)."
                )
            ev_input = evidence_validation_input_from_payload(input_payload)
            result = await self.evidence_validation_service.investigate(ev_input)
            return evidence_validation_result_to_payload(result)

        if agent_type is AgentType.SEARCH_PLANNING:
            if self.search_planning_service is None:
                raise AgentServiceUnavailableError(
                    "Search planning service nao configurado (verifique GEMINI_API_KEY)."
                )
            sp_input = search_plan_input_from_payload(input_payload)
            result = await self.search_planning_service.plan_searches(sp_input)
            return search_plan_result_to_payload(result)

        raise UnsupportedAgentJobError(
            f"Agent type '{agent_type}' ainda nao tem grafo configurado."
        )
