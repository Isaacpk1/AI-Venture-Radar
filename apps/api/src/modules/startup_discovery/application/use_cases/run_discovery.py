"""Caso de uso principal: descobre startups em hubs publicos.

Fluxo por run:
  1. Cria e persiste um DiscoveryRun (pending -> running).
  2. Para cada hub do registry, chama o extrator correspondente para
     obter URLs de startups.
  3. Limita o total a `max_per_run` URLs.
  4. Cada URL e submetida como `url_ingestion_job` com
     `source_type="startup_evidence"` — o pipeline existente cuida do
     resto (scraping, ingestion, embeddings, analise).
  5. Salva o resultado agregado no DiscoveryRun (completed ou failed).

Um hub que falha nao cancela os outros — best-effort. O run so falha
inteiro se TODOS os hubs falharem.
"""

from typing import Callable

from apps.api.src.modules.startup_discovery.application.dto import (
    DiscoveryRunView,
    SubmittedUrlView,
)
from apps.api.src.modules.startup_discovery.application.ports import HubLinkExtractor
from apps.api.src.modules.startup_discovery.domain.entities import DiscoveryRun
from apps.api.src.modules.startup_discovery.domain.hub_registry import HUB_SOURCES
from apps.api.src.shared.logging import get_logger

logger = get_logger(__name__)


class RunStartupDiscovery:

    def __init__(
        self,
        *,
        uow_factory: Callable,
        extractors: dict[str, HubLinkExtractor],
        url_ingestion_submitter,
        max_per_run: int = 20,
    ) -> None:
        self._uow_factory = uow_factory
        self._extractors = extractors
        self._submitter = url_ingestion_submitter
        self._max_per_run = max_per_run

    async def execute(self) -> DiscoveryRunView:
        run = DiscoveryRun()
        await self._save(run)

        run.start()
        await self._save(run)

        submitted_urls: list[SubmittedUrlView] = []
        hubs_processed = 0
        had_success = False

        for hub in HUB_SOURCES:
            if len(submitted_urls) >= self._max_per_run:
                break

            extractor = self._extractors.get(hub.extractor_type)
            if extractor is None:
                logger.warning(
                    "no extractor for hub, skipping",
                    extra={"hub": hub.name, "extractor_type": hub.extractor_type},
                )
                continue

            remaining = self._max_per_run - len(submitted_urls)
            try:
                urls = await extractor.extract(hub.listing_url, limit=remaining)
                had_success = True
            except Exception as exc:
                logger.warning(
                    "hub extractor failed, skipping hub",
                    extra={"hub": hub.name, "reason": str(exc)},
                )
                continue

            hubs_processed += 1
            logger.info(
                "hub extracted",
                extra={"hub": hub.name, "urls_found": len(urls)},
            )

            for url in urls:
                try:
                    job_id = await self._submitter.submit(url)
                    submitted_urls.append(
                        SubmittedUrlView(hub_name=hub.name, url=url, job_id=job_id)
                    )
                    logger.info(
                        "url_ingestion_job submitted",
                        extra={"hub": hub.name, "url": url, "job_id": str(job_id)},
                    )
                except Exception as exc:
                    logger.warning(
                        "failed to submit url_ingestion_job",
                        extra={"url": url, "reason": str(exc)},
                    )

        if not had_success and HUB_SOURCES:
            run.fail("Todos os hubs falharam na extracao de links.")
        else:
            run.complete(
                hubs_processed=hubs_processed,
                urls_found=len(submitted_urls),
                jobs_submitted=len(submitted_urls),
            )

        await self._save(run)
        return _to_view(run, submitted_urls)

    async def _save(self, run: DiscoveryRun) -> None:
        async with self._uow_factory() as uow:
            await uow.repository.save(run)
            await uow.commit()


def _to_view(run: DiscoveryRun, submitted: list[SubmittedUrlView]) -> DiscoveryRunView:
    return DiscoveryRunView(
        id=run.id,
        status=run.status,
        hubs_processed=run.hubs_processed,
        urls_found=run.urls_found,
        jobs_submitted=run.jobs_submitted,
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
        submitted_urls=submitted,
    )
