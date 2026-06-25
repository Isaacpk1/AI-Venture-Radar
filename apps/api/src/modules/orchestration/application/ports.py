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
    async def submit(self, url: str, *, source_type: str = "startup_evidence") -> UUID:
        """Submete a URL e devolve o scraping_job_id."""

    @abstractmethod
    async def get_status(self, job_id: UUID) -> StepStatus:
        """Consulta o status; ``result_id`` e' o scraping_result_id quando concluido."""


@dataclass(frozen=True)
class DocumentContentView:
    """Conteudo do documento ingerido, vocabulario proprio de orchestration."""

    title: str | None
    clean_text: str


class IngestionPort(ABC):
    """Contrato para submeter e acompanhar um job de ingestion (Orchestration V2)."""

    @abstractmethod
    async def submit(
        self,
        scraping_result_id: UUID,
        *,
        source_type: str = "startup_evidence",
    ) -> UUID:
        """Submete o scraping_result_id e devolve o ingestion_job_id."""

    @abstractmethod
    async def get_status(self, job_id: UUID) -> StepStatus:
        """Consulta o status; ``result_id`` e' o document_id quando concluido."""

    @abstractmethod
    async def get_document_content(
        self, scraping_result_id: UUID
    ) -> DocumentContentView | None:
        """Le titulo e texto limpo do documento ingerido, ou ``None``."""


class EmbeddingsPort(ABC):
    """Contrato para submeter e acompanhar um job de embeddings (Orchestration V2)."""

    @abstractmethod
    async def submit(self, document_id: UUID) -> UUID:
        """Submete o document_id e devolve o embedding_job_id."""

    @abstractmethod
    async def get_status(self, job_id: UUID) -> StepStatus:
        """Consulta o status; ``result_id`` sempre None (ultimo passo)."""

    @abstractmethod
    async def delete_vectors_for_document(self, document_id: UUID) -> None:
        """Remove os vetores de um documento superado por um re-scrape.

        Best-effort do ponto de vista de quem chama: nao impede a
        conclusao do job se falhar, so deixa o vetor orfao pra uma limpeza
        futura.
        """


class UrlIngestionTaskDispatcher(ABC):
    """Porta para publicar/reenfileirar um url ingestion job na fila."""

    @abstractmethod
    async def dispatch(self, *, job_id: UUID) -> None:
        """Publica o job_id na fila de url ingestion."""


class StartupsPort(ABC):
    """Contrato para criar/enriquecer o perfil de uma startup a partir de
    conteudo ja ingerido (Orchestration V2). Vocabulario proprio de
    orchestration, decoupled dos DTOs internos de ``startups``."""

    @abstractmethod
    async def create_startup(self, *, name: str, website_url: str) -> UUID:
        """Cria a startup e devolve seu id."""

    @abstractmethod
    async def attach_evidence(
        self,
        *,
        startup_id: UUID,
        scraping_result_id: UUID,
        source_url: str,
        title: str | None,
        notes: str | None,
    ) -> None:
        """Associa o conteudo ingerido como evidencia da startup."""

    @abstractmethod
    async def try_extract(self, startup_id: UUID) -> None:
        """Aciona a extracao estruturada; nao-op se o servico nao estiver disponivel."""

    @abstractmethod
    async def try_classify(self, startup_id: UUID) -> None:
        """Aciona a classificacao de maturidade de IA; nao-op se o servico nao estiver disponivel."""
