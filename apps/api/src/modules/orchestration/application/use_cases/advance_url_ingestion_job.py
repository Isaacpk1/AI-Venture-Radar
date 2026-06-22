"""Caso de uso que avanca a maquina de estados de um url ingestion job.

Chamado a cada entrega da fila ``url_ingestion`` (worker). So avanca UM
passo por chamada: submete o proximo job downstream quando o atual
terminou, ou levanta ``UrlIngestionStillProcessingError`` para o
Dramatiq reentregar a mensagem mais tarde enquanto espera. Mesmo padrao
de retry-via-excecao ja usado por ``ExecuteEmbeddingJob`` para chunks
pendentes.
"""

from uuid import UUID

from apps.api.src.modules.orchestration.application.ports import (
    EmbeddingsPort,
    IngestionPort,
    ScrapingPort,
)
from apps.api.src.modules.orchestration.application.unit_of_work import (
    AnalysisUnitOfWorkFactory,
)
from apps.api.src.modules.orchestration.domain.entities import UrlIngestionJob
from apps.api.src.modules.orchestration.domain.enums import UrlIngestionJobStatus
from apps.api.src.modules.orchestration.domain.exceptions import (
    UrlIngestionJobNotFoundError,
    UrlIngestionStillProcessingError,
)


class AdvanceUrlIngestionJob:

    def __init__(
        self,
        uow_factory: AnalysisUnitOfWorkFactory,
        scraping_port: ScrapingPort,
        ingestion_port: IngestionPort,
        embeddings_port: EmbeddingsPort,
    ) -> None:
        self._uow_factory = uow_factory
        self._scraping_port = scraping_port
        self._ingestion_port = ingestion_port
        self._embeddings_port = embeddings_port

    async def execute(self, *, job_id: UUID) -> None:
        job = await self._get(job_id)

        if job.status is UrlIngestionJobStatus.PENDING:
            scraping_job_id = await self._scraping_port.submit(job.url)
            job.start_scraping(scraping_job_id)
            await self._save(job)
            raise UrlIngestionStillProcessingError("Scraping submetido.")

        if job.status is UrlIngestionJobStatus.SCRAPING:
            assert job.scraping_job_id is not None
            status = await self._scraping_port.get_status(job.scraping_job_id)
            if status.is_failed:
                job.fail(status.error_message or "Scraping falhou.")
                await self._save(job)
                return
            if not status.is_done:
                raise UrlIngestionStillProcessingError("Scraping em andamento.")

            assert status.result_id is not None
            ingestion_job_id = await self._ingestion_port.submit(
                status.result_id,
                source_type=job.source_type,
            )
            job.start_ingesting(
                scraping_result_id=status.result_id,
                ingestion_job_id=ingestion_job_id,
            )
            await self._save(job)
            raise UrlIngestionStillProcessingError("Ingestion submetido.")

        if job.status is UrlIngestionJobStatus.INGESTING:
            assert job.ingestion_job_id is not None
            status = await self._ingestion_port.get_status(job.ingestion_job_id)
            if status.is_failed:
                job.fail(status.error_message or "Ingestion falhou.")
                await self._save(job)
                return
            if not status.is_done:
                raise UrlIngestionStillProcessingError("Ingestion em andamento.")

            assert status.result_id is not None
            embedding_job_id = await self._embeddings_port.submit(status.result_id)
            job.start_embedding(
                document_id=status.result_id,
                embedding_job_id=embedding_job_id,
            )
            await self._save(job)
            raise UrlIngestionStillProcessingError("Embedding submetido.")

        if job.status is UrlIngestionJobStatus.EMBEDDING:
            assert job.embedding_job_id is not None
            status = await self._embeddings_port.get_status(job.embedding_job_id)
            if status.is_failed:
                job.fail(status.error_message or "Embedding falhou.")
                await self._save(job)
                return
            if not status.is_done:
                raise UrlIngestionStillProcessingError("Embedding em andamento.")

            job.complete()
            await self._save(job)
            return

        # COMPLETED/FAILED: estado terminal, nada a fazer.
        return

    async def _get(self, job_id: UUID) -> UrlIngestionJob:
        async with self._uow_factory() as uow:
            job = await uow.url_ingestion_job_repository.get_by_id(job_id)
            if job is None:
                raise UrlIngestionJobNotFoundError(
                    f"UrlIngestionJob {job_id} nao encontrado."
                )
            return job

    async def _save(self, job: UrlIngestionJob) -> None:
        async with self._uow_factory() as uow:
            await uow.url_ingestion_job_repository.save(job)
            await uow.commit()
