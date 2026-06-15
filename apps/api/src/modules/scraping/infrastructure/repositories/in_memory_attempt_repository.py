"""Repositório temporário de tentativas armazenadas em memória."""

from copy import deepcopy
from uuid import UUID

from apps.api.src.modules.scraping.domain.entities import ScrapingAttempt
from apps.api.src.modules.scraping.domain.repositories import (
    ScrapingAttemptRepository,
)


class InMemoryScrapingAttemptRepository(ScrapingAttemptRepository):
    """Implementa persistência e consulta das tentativas de scraping."""

    def __init__(self) -> None:
        # O ID da tentativa identifica o registro que será criado ou atualizado.
        self._attempts: dict[UUID, ScrapingAttempt] = {}

    async def save(self, attempt: ScrapingAttempt) -> None:
        """Cria ou atualiza uma tentativa usando seu identificador."""

        self._attempts[attempt.id] = deepcopy(attempt)

    async def list_by_job_id(self, job_id: UUID) -> list[ScrapingAttempt]:
        """Lista somente as tentativas pertencentes ao job informado."""

        attempts = [
            attempt
            for attempt in self._attempts.values()
            if attempt.job_id == job_id
        ]

        # A ordem cronológica permite reconstruir exatamente o fluxo:
        # BeautifulSoup tentou primeiro, depois Playwright, e assim por diante.
        attempts.sort(key=lambda attempt: attempt.started_at)

        return deepcopy(attempts)
