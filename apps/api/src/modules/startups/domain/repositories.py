"""Contratos de persistencia do modulo startups."""

from abc import ABC, abstractmethod
from uuid import UUID

from apps.api.src.modules.startups.domain.entities import Startup, StartupEvidence
from apps.api.src.modules.startups.domain.enums import AiMaturityLevel


class StartupRepository(ABC):

    @abstractmethod
    async def save(self, startup: Startup) -> None:
        """Cria ou atualiza uma startup."""

    @abstractmethod
    async def get_by_id(self, startup_id: UUID) -> Startup | None:
        """Busca startup por id."""

    @abstractmethod
    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        query: str | None = None,
        sector: str | None = None,
        country: str | None = None,
        ai_maturity_level: AiMaturityLevel | None = None,
    ) -> tuple[list[Startup], int]:
        """Lista startups filtradas, ordenadas pela atualizacao mais recente."""


class StartupEvidenceRepository(ABC):

    @abstractmethod
    async def save(self, evidence: StartupEvidence) -> None:
        """Cria ou atualiza uma evidencia."""

    @abstractmethod
    async def get_by_id(self, evidence_id: UUID) -> StartupEvidence | None:
        """Busca evidencia por id."""

    @abstractmethod
    async def list_by_startup_id(self, startup_id: UUID) -> list[StartupEvidence]:
        """Lista evidencias associadas a uma startup."""
