"""Portas do modulo agents.

Portas sao contratos que a camada de aplicacao usa para falar com capacidades
externas. Aqui, o agents precisa publicar execucoes longas em fila, mas nao
deve conhecer Redis ou Dramatiq diretamente.
"""

from abc import ABC, abstractmethod
from uuid import UUID


class AgentTaskDispatcher(ABC):
    """Contrato para enviar uma execucao de agente a um worker externo."""

    @abstractmethod
    async def dispatch(
        self,
        *,
        run_id: UUID,
    ) -> None:
        """Publica somente o identificador da execucao para o worker."""
