"""Actors Dramatiq executados pelo worker de scraping."""

from uuid import UUID

import dramatiq

# Este import configura o RedisBroker e o middleware AsyncIO antes de o actor
# abaixo ser registrado. O nome importado tambem e passado explicitamente ao
# decorator para deixar clara a dependencia da task.
from apps.api.src.modules.scraping.infrastructure.queue.dramatiq_broker import (
    broker,
)
from apps.api.src.modules.scraping.factories.scraping_factory import ScrapingFactory


@dramatiq.actor(
    broker=broker,
    queue_name="scraping",
    max_retries=3,
)
async def execute_scraping_job(job_id: str) -> None:
    """Executa um job existente usando a logica do modulo de scraping.

    O Redis transporta somente a string do UUID. A task converte esse valor e
    chama o caso de uso pela factory; ela nao implementa scraping, persistencia
    ou regras de negocio.
    """

    use_case = ScrapingFactory.create_execute_scraping_job()
    await use_case.execute(UUID(job_id))
