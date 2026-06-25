"""Contratos (ports) que a aplicacao define e a infraestrutura implementa."""

from abc import ABC, abstractmethod


class HubLinkExtractor(ABC):
    """Extrai URLs de startups de uma pagina de listagem de hub."""

    @abstractmethod
    async def extract(self, listing_url: str, *, limit: int) -> list[str]: ...


class StartupUrlIngestionSubmitter(ABC):
    """Submete uma URL de startup ao pipeline de url_ingestion_jobs."""

    @abstractmethod
    async def submit(self, url: str) -> object: ...
