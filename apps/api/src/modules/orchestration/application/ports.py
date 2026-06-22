"""Portas que conectam a aplicacao de orchestration a outros modulos.

``orchestration`` mantem seu proprio vocabulario, decoupled das views
exatas de ``recommendations`` e ``briefing``. As implementacoes concretas
destas portas vivem em ``infrastructure/`` e sao o unico lugar que conhece
os contratos publicos dos dois modulos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


class RecommendationsPort(ABC):
    """Contrato para disparar a geracao de recomendacoes de uma startup."""

    @abstractmethod
    async def generate(self, startup_id: UUID) -> int:
        """Gera as recomendacoes e retorna quantas foram criadas."""


class BriefingPort(ABC):
    """Contrato para disparar a geracao do briefing de uma startup."""

    @abstractmethod
    async def generate(self, startup_id: UUID) -> UUID:
        """Gera o briefing e retorna o id do briefing criado."""


@dataclass(frozen=True)
class StepStatus:
    """Vocabulario simplificado e proprio de orchestration para o status de
    um job downstream (scraping/ingestion/embeddings) — decoupled das views
    exatas de cada modulo, mesmo espirito de ``RecommendationsPort``/
    ``BriefingPort``."""

    is_done: bool
    is_failed: bool
    result_id: UUID | None
    error_message: str | None


class ScrapingPort(ABC):
    """Contrato para submeter e acompanhar um job de scraping (Orchestration V2)."""

    @abstractmethod
    async def submit(self, url: str) -> UUID:
        """Submete a URL e devolve o scraping_job_id."""

    @abstractmethod
    async def get_status(self, job_id: UUID) -> StepStatus:
        """Consulta o status; ``result_id`` e' o scraping_result_id quando concluido."""


class IngestionPort(ABC):
    """Contrato para submeter e acompanhar um job de ingestion (Orchestration V2)."""

    @abstractmethod
    async def submit(self, scraping_result_id: UUID) -> UUID:
        """Submete o scraping_result_id e devolve o ingestion_job_id."""

    @abstractmethod
    async def get_status(self, job_id: UUID) -> StepStatus:
        """Consulta o status; ``result_id`` e' o document_id quando concluido."""


class EmbeddingsPort(ABC):
    """Contrato para submeter e acompanhar um job de embeddings (Orchestration V2)."""

    @abstractmethod
    async def submit(self, document_id: UUID) -> UUID:
        """Submete o document_id e devolve o embedding_job_id."""

    @abstractmethod
    async def get_status(self, job_id: UUID) -> StepStatus:
        """Consulta o status; ``result_id`` sempre None (ultimo passo)."""


class UrlIngestionTaskDispatcher(ABC):
    """Porta para publicar/reenfileirar um url ingestion job na fila."""

    @abstractmethod
    async def dispatch(self, *, job_id: UUID) -> None:
        """Publica o job_id na fila de url ingestion."""
