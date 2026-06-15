"""Contrato publico do Search Planner Agent.

Outros modulos devem depender deste contrato, nao de LangGraph, LangChain ou
Gemini diretamente. Assim, a implementacao interna pode mudar sem quebrar quem
consome o plano de busca.
"""

from abc import ABC, abstractmethod

from apps.api.src.modules.agents.application.dto import (
    SearchPlanInput,
    SearchPlanResult,
)


class SearchPlanningService(ABC):
    """Planeja novas buscas quando uma evidencia ainda nao e suficiente."""

    @abstractmethod
    async def plan_searches(
        self,
        plan_input: SearchPlanInput,
    ) -> SearchPlanResult:
        """Recebe um caso incompleto e devolve queries priorizadas."""
