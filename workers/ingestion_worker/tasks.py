"""Actors Dramatiq executados pelo worker de ingestion."""

from uuid import UUID

import dramatiq

from apps.api.src.shared.queue.dramatiq_broker import broker
from apps.api.src.modules.ingestion.factories.ingestion_factory import IngestionFactory


@dramatiq.actor(
    broker=broker,
    queue_name="ingestion",
    max_retries=3,
)
async def execute_ingestion_job(job_id: str) -> None:
    """Executa um job de ingestion recebido da fila.

    O worker transporta apenas o job_id. Toda a logica de limpeza,
    chunking e persistencia fica no modulo de ingestion.
    """

    use_case = IngestionFactory.create_execute_ingestion_job()
    await use_case.execute(job_id=UUID(job_id))
