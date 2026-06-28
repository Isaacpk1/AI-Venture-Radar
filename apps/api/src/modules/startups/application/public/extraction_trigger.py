"""Contrato publico para acionar extracao estruturada a partir de outro modulo."""

from abc import ABC, abstractmethod
from uuid import UUID


class ExtractionTrigger(ABC):
    """Extracao best-effort consumivel por orchestration e outros modulos.

    Implementacoes nao devem propagar a indisponibilidade do servico de
    extracao (ex: sem GEMINI_API_KEY) — quem chama nao deve precisar
    conhecer esse vocabulario interno do modulo startups.
    """

    @abstractmethod
    async def try_extract(self, startup_id: UUID) -> None:
        """Extrai founders/funding/customers; nao-op se o servico nao estiver disponivel."""
