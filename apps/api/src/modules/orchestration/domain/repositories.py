"""Contratos de persistencia do modulo orchestration."""

from abc import ABC, abstractmethod
from uuid import UUID

from apps.api.src.modules.orchestration.domain.entities import (
    AnalysisJob,
    UrlIngestionJob,
)


class AnalysisJobRepository(ABC):

    @abstractmethod
    async def save(self, analysis_job: AnalysisJob) -> None:
        """Cria ou atualiza um analysis job."""

    @abstractmethod
    async def get_by_id(self, analysis_job_id: UUID) -> AnalysisJob | None:
        """Busca analysis job por id."""

    @abstractmethod
    async def list_by_startup_id(self, startup_id: UUID) -> list[AnalysisJob]:
        """Lista o historico de execucoes de uma startup, mais recentes primeiro."""


class UrlIngestionJobRepository(ABC):

    @abstractmethod
    async def save(self, job: UrlIngestionJob) -> None:
        """Cria ou atualiza um url ingestion job."""

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> UrlIngestionJob | None:
        """Busca url ingestion job por id."""
