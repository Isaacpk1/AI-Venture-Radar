"""Portas que conectam a aplicação às tecnologias externas.

Uma porta é um contrato definido pelo lado que precisa da capacidade. A camada
de aplicação precisa coletar páginas, validar resultados e enviar jobs, mas não
deve conhecer BeautifulSoup, HTTP, Redis ou Dramatiq diretamente.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from apps.api.src.modules.scraping.domain.enums import ScrapingMethod

from .dto import DeterministicValidationResult, ScrapingInput, ScrapingOutput


class Scraper(ABC):
    """Contrato implementado por cada tecnologia de coleta."""

    # Cada implementação informa qual método utiliza. Isso permite registrar a
    # tecnologia usada em ScrapingAttempt e ScrapingResult.
    method: ScrapingMethod

    @abstractmethod
    async def scrape(self, scraping_input: ScrapingInput) -> ScrapingOutput:
        """Coleta uma página e devolve o formato padronizado da aplicação."""


class DeterministicValidator(ABC):
    """Contrato para validações objetivas, sem uso de LLM."""

    @abstractmethod
    async def validate(
        self,
        output: ScrapingOutput,
    ) -> DeterministicValidationResult:
        """Avalia aspectos técnicos, textuais e evidenciais básicos."""


class TaskDispatcher(ABC):
    """Contrato para enviar um job a um executor externo.

    Futuramente, uma implementação usará Redis e Dramatiq. Inicialmente,
    poderemos utilizar uma implementação local sem alterar os casos de uso.
    """

    @abstractmethod
    async def dispatch(self, job_id: UUID) -> None:
        """Envia somente o identificador do job para execução."""
