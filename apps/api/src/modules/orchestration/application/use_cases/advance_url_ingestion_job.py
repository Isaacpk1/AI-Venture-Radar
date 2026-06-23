"""Caso de uso que avanca a maquina de estados de um url ingestion job.

Chamado a cada entrega da fila ``url_ingestion`` (worker). So avanca UM
passo por chamada: submete o proximo job downstream quando o atual
terminou, ou levanta ``UrlIngestionStillProcessingError`` para o
Dramatiq reentregar a mensagem mais tarde enquanto espera. Mesmo padrao
de retry-via-excecao ja usado por ``ExecuteEmbeddingJob`` para chunks
pendentes.

A etapa ``ANALYZING`` e diferente das anteriores: nao submete um job
assincrono de outro modulo para ficar consultando depois — startup,
evidencia, extract, classify, recommendations e briefing sao chamadas
sincronas (mesmo padrao que ``ExecuteAnalysisJob`` ja usa para
recommendations->briefing), entao a cadeia inteira roda numa unica
entrega. Falha aqui e terminal (``job.fail()``, sem relancar) — nao e o
padrao "ainda processando" usado para scraping/ingestion/embedding, que
sao jobs assincronos de outro modulo. As escritas intermediarias
(``link_startup``/``mark_evidence_attached``) existem para proteger
contra reentrega-por-crash do Dramatiq: se o processo morrer entre criar
a startup e salvar o job, a proxima entrega nao deve criar uma segunda
startup nem duplicar a evidencia.
"""

from urllib.parse import urlparse
from uuid import UUID

from apps.api.src.modules.orchestration.application.ports import (
    BriefingPort,
    EmbeddingsPort,
    IngestionPort,
    RecommendationsPort,
    ScrapingPort,
    StartupsPort,
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
from apps.api.src.shared.logging import bind_context, get_logger

STARTUP_EVIDENCE_SOURCE_TYPE = "startup_evidence"
MAX_EVIDENCE_TEXT_CHARS = 8000

logger = get_logger(__name__)


def _derive_startup_name(*, title: str | None, url: str) -> str:
    if title:
        return title
    hostname = urlparse(url).netloc
    return hostname.removeprefix("www.") or url


class AdvanceUrlIngestionJob:

    def __init__(
        self,
        uow_factory: AnalysisUnitOfWorkFactory,
        scraping_port: ScrapingPort,
        ingestion_port: IngestionPort,
        embeddings_port: EmbeddingsPort,
        startups_port: StartupsPort,
        recommendations_port: RecommendationsPort,
        briefing_port: BriefingPort,
    ) -> None:
        self._uow_factory = uow_factory
        self._scraping_port = scraping_port
        self._ingestion_port = ingestion_port
        self._embeddings_port = embeddings_port
        self._startups_port = startups_port
        self._recommendations_port = recommendations_port
        self._briefing_port = briefing_port

    async def execute(self, *, job_id: UUID) -> None:
        job = await self._get(job_id)

        with bind_context(job_id=str(job_id)):
            logger.info(
                "advancing url ingestion job", extra={"status": job.status.value}
            )

            if job.status is UrlIngestionJobStatus.PENDING:
                scraping_job_id = await self._scraping_port.submit(
                    job.url, source_type=job.source_type
                )
                job.start_scraping(scraping_job_id)
                await self._save(job)
                raise UrlIngestionStillProcessingError("Scraping submetido.")

            if job.status is UrlIngestionJobStatus.SCRAPING:
                assert job.scraping_job_id is not None
                status = await self._scraping_port.get_status(job.scraping_job_id)
                if status.is_failed:
                    logger.warning(
                        "scraping failed, failing url ingestion job",
                        extra={"reason": status.error_message},
                    )
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
                    logger.warning(
                        "ingestion failed, failing url ingestion job",
                        extra={"reason": status.error_message},
                    )
                    job.fail(status.error_message or "Ingestion falhou.")
                    await self._save(job)
                    return
                if not status.is_done:
                    raise UrlIngestionStillProcessingError("Ingestion em andamento.")

                assert status.result_id is not None
                embedding_job_id = await self._embeddings_port.submit(
                    status.result_id
                )
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
                    logger.warning(
                        "embedding failed, failing url ingestion job",
                        extra={"reason": status.error_message},
                    )
                    job.fail(status.error_message or "Embedding falhou.")
                    await self._save(job)
                    return
                if not status.is_done:
                    raise UrlIngestionStillProcessingError("Embedding em andamento.")

                if job.source_type != STARTUP_EVIDENCE_SOURCE_TYPE:
                    job.complete()
                    await self._save(job)
                    return

                job.start_analyzing()
                await self._save(job)
                raise UrlIngestionStillProcessingError(
                    "Embedding concluido, iniciando analise."
                )

            if job.status is UrlIngestionJobStatus.ANALYZING:
                assert job.scraping_result_id is not None
                try:
                    await self._run_analysis(job)
                except Exception as error:
                    logger.warning(
                        "analysis failed, failing url ingestion job",
                        extra={"reason": str(error)},
                    )
                    job.fail(str(error))
                    await self._save(job)
                    return

                job.complete()
                await self._save(job)
                logger.info(
                    "url ingestion job completed",
                    extra={
                        "startup_id": str(job.startup_id),
                        "recommendation_count": job.recommendation_count,
                        "briefing_id": str(job.briefing_id),
                    },
                )
                return

            # COMPLETED/FAILED: estado terminal, nada a fazer.
            return

    async def _run_analysis(self, job: UrlIngestionJob) -> None:
        assert job.scraping_result_id is not None
        content = await self._ingestion_port.get_document_content(
            job.scraping_result_id
        )

        if job.startup_id is None:
            name = _derive_startup_name(
                title=content.title if content else None, url=job.url
            )
            startup_id = await self._startups_port.create_startup(
                name=name, website_url=job.url
            )
            job.link_startup(startup_id)
            await self._save(job)
            logger.info(
                "startup created from url ingestion job",
                extra={"startup_id": str(startup_id)},
            )

        assert job.startup_id is not None

        with bind_context(startup_id=str(job.startup_id)):
            if not job.evidence_attached:
                notes = (
                    content.clean_text[:MAX_EVIDENCE_TEXT_CHARS] if content else None
                )
                title = content.title if content else None
                await self._startups_port.attach_evidence(
                    startup_id=job.startup_id,
                    scraping_result_id=job.scraping_result_id,
                    source_url=job.url,
                    title=title,
                    notes=notes,
                )
                job.mark_evidence_attached()
                await self._save(job)
                logger.info("evidence attached to startup")

            logger.info("running extraction (best-effort)")
            await self._startups_port.try_extract(job.startup_id)

            logger.info("running classification (best-effort)")
            await self._startups_port.try_classify(job.startup_id)

            recommendation_count = await self._recommendations_port.generate(
                job.startup_id
            )
            logger.info(
                "recommendations generated",
                extra={"recommendation_count": recommendation_count},
            )

            briefing_id = await self._briefing_port.generate(job.startup_id)
            logger.info("briefing generated", extra={"briefing_id": str(briefing_id)})

            job.record_analysis_result(
                recommendation_count=recommendation_count, briefing_id=briefing_id
            )

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
