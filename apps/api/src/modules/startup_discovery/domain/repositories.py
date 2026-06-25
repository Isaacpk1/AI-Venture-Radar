"""Contratos de persistencia do modulo startup_discovery."""

from abc import ABC, abstractmethod
from uuid import UUID

from apps.api.src.modules.startup_discovery.domain.entities import DiscoveryRun


class DiscoveryRunRepository(ABC):

    @abstractmethod
    async def save(self, run: DiscoveryRun) -> None:
        """Cria ou atualiza um discovery run."""

    @abstractmethod
    async def get_by_id(self, run_id: UUID) -> DiscoveryRun | None:
        """Busca discovery run por id."""

    @abstractmethod
    async def list_recent(self, *, limit: int = 20) -> list[DiscoveryRun]:
        """Lista os runs mais recentes, do mais novo para o mais antigo."""
