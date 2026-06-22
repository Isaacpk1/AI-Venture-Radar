"""Portas do modulo agents.

Portas sao contratos que a camada de aplicacao usa para falar com capacidades
externas. Aqui, o agents precisa publicar execucoes longas em fila, mas nao
deve conhecer Redis ou Dramatiq diretamente. Tambem usa portas para chamar
outros modulos como "tool" (ex: NVIDIA RAG Agent chamando ``rag``), mantendo
``agents`` sem dependencia direta dos DTOs do modulo externo.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from apps.api.src.modules.agents.application.dto import NvidiaRagResult


class AgentTaskDispatcher(ABC):
    """Contrato para enviar uma execucao de agente a um worker externo."""

    @abstractmethod
    async def dispatch(
        self,
        *,
        run_id: UUID,
    ) -> None:
        """Publica somente o identificador da execucao para o worker."""


class NvidiaRagToolPort(ABC):
    """Contrato interno para consultar a base de conhecimento NVIDIA via RAG.

    Vocabulario simplificado e proprio de ``agents`` (so query/limit na
    entrada, ``NvidiaRagResult`` na saida) — decoupled das DTOs exatas de
    ``rag``. A traducao e responsabilidade do adaptador concreto
    (``infrastructure/rag_adapters/``).
    """

    @abstractmethod
    async def answer(self, query: str, *, limit: int = 5) -> NvidiaRagResult:
        """Recupera evidencias da base NVIDIA e devolve resposta com citacoes."""
