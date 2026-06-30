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

import re
from urllib.parse import urljoin, urlparse, urlunparse
from uuid import UUID

from apps.api.src.modules.orchestration.application.ports import (
    BriefingPort,
    DocumentContentView,
    EmbeddingsPort,
    EnrichmentSearchExecutorPort,
    EnrichmentSearchPlannerPort,
    IngestionPort,
    RecommendationsPort,
    ScrapingPort,
    StartupProfileSnapshot,
    StartupsPort,
    UrlIngestionTaskDispatcher,
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
MAX_ENRICHMENT_ROUNDS = 1
MAX_ENRICHMENT_URLS_PER_ROUND = 4
MAX_ENRICHMENT_SEARCH_QUERIES = 3
MAX_ENRICHMENT_SEARCH_RESULTS_PER_QUERY = 5

# Paths that commonly reveal tech stack, team, and traction — ordered by signal value.
ENRICHMENT_PATHS = (
    "product",
    "products",
    "solution",
    "solutions",
    "platform",
    "technology",
    "careers",
    "jobs",
    "carreiras",
    "trabalhe-conosco",
    "engineering",
    "blog",
    "about",
    "sobre",
    "team",
    "customers",
    "case-studies",
)
TRUSTED_ENRICHMENT_HOSTS = {
    "crunchbase.com",
    "www.crunchbase.com",
    "linkedin.com",
    "www.linkedin.com",
    "wellfound.com",
    "www.wellfound.com",
    # Bases de dados de startups / investimentos
    "angel.co",
    "pitchbook.com",
    "tracxn.com",
    "f6s.com",
    # Public job boards often expose stack and deployment hints.
    "gupy.io",
    "boards.greenhouse.io",
    "jobs.lever.co",
}
AI_EVIDENCE_TERMS = (
    " ai ",
    " ai-",
    " ai.",
    "artificial intelligence",
    "inteligencia artificial",
    "inteligência artificial",
    "machine learning",
    "deep learning",
    "generative ai",
    "gen ai",
    "llm",
    "large language model",
    "computer vision",
    "natural language",
    "nlp",
    "neural network",
    "model training",
    "model inference",
    "foundation model",
    "agentic",
    "automation with ai",
)
BLOCKED_ENRICHMENT_HOSTS = {
    # Redes sociais — conteudo fragmentado, sem informacao estruturada de empresa
    "facebook.com",
    "instagram.com",
    "linktr.ee",
    "tiktok.com",
    "threads.net",
    "twitter.com",
    "x.com",
    # Agregadores de conteudo — nao autoritativos sobre a empresa
    "reddit.com",
    "quora.com",
    "medium.com",
    "substack.com",
    "grokipedia.com",
    "wikipedia.org",
    # Video / streaming
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    # Avaliacoes — util para cultura, nao para perfil tecnico de empresa
    "glassdoor.com",
    "indeed.com",
    "vagas.com.br",
    "catho.com.br",
    # SEO farms / diretórios de baixa qualidade
    "yellowpages.com",
    "yelp.com",
}

logger = get_logger(__name__)


# Generic page-type words that appear as fragments in HTML titles.
_GENERIC_PAGE_FRAGMENT_RE = re.compile(
    r"^(?:home|about(?:\s+us)?|quem\s+somos|inicio|"
    r"bem[- ]vindo(?:s)?|nossa\s+empresa|company|welcome|"
    r"official\s+site|website|contact(?:o)?|"
    r"products?|solutions?|servi[cç]os?|platform)$",
    re.IGNORECASE,
)

# Known multi-segment TLDs (order matters: longest first).
_MULTI_TLDS = ("com.br", "co.uk", "org.br", "net.br", "gov.br", "co.in")


def _domain_to_brand(hostname: str) -> str:
    """Extract a readable brand name from a hostname.

    'plat.econodata.com.br' -> 'Econodata'
    'www.aprix.ai'          -> 'Aprix'
    'app.datlo.io'          -> 'Datlo'
    """
    h = hostname.lower().removeprefix("www.")
    # Strip known multi-segment TLDs first
    for tld in _MULTI_TLDS:
        if h.endswith(f".{tld}"):
            h = h[: -(len(tld) + 1)]
            break
    # Remove any remaining TLD (.ai, .io, .com, etc.)
    if "." in h:
        h = h.rsplit(".", 1)[0]
    # Strip any leading subdomain (app., plat., api., staging., etc.)
    if "." in h:
        h = h.rsplit(".", 1)[-1]
    return h.capitalize() if h else hostname


def _clean_page_title(title: str) -> str:
    """Remove generic page-type fragments from an HTML title.

    'About us - Aprix Pricing'  -> 'Aprix Pricing'
    'Home | Econodata'          -> 'Econodata'
    'NeuralMind – AI solutions' -> 'NeuralMind'
    """
    for sep in (" - ", " | ", " – ", " — ", " • ", " / ", " \\ "):
        if sep in title:
            parts = [p.strip() for p in title.split(sep)]
            meaningful = [
                p for p in parts if p and not _GENERIC_PAGE_FRAGMENT_RE.match(p)
            ]
            if meaningful:
                # Prefer the shortest non-generic part (usually the brand).
                return min(meaningful, key=len)
    return title.strip()


def _derive_startup_name(*, title: str | None, url: str) -> str:
    hostname = urlparse(url).netloc
    brand_from_domain = _domain_to_brand(hostname) if hostname else url

    if title:
        cleaned = _clean_page_title(title)
        # Fall back to domain-derived name when the cleaned title is still
        # a hostname (nothing meaningful was in the title).
        if cleaned.lower() in (hostname.lower(), hostname.lower().removeprefix("www.")):
            return brand_from_domain
        return cleaned

    return brand_from_domain


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def _same_domain_candidate_urls(source_url: str) -> list[str]:
    parsed = urlparse(source_url)
    if not parsed.netloc:
        return []

    base = urlunparse((parsed.scheme or "https", parsed.netloc, "/", "", "", ""))
    return [_normalize_url(urljoin(base, path)) for path in ENRICHMENT_PATHS]


def _hostname(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _startup_terms(name: str) -> list[str]:
    return [
        term
        for term in (
            name.lower()
            .replace(".", " ")
            .replace("-", " ")
            .replace("_", " ")
            .split()
        )
        if len(term) >= 4
    ]


def _has_ai_evidence_signal(text: str) -> bool:
    normalized = f" {text.lower()} "
    return any(term in normalized for term in AI_EVIDENCE_TERMS)


def _score_external_candidate(
    *,
    url: str,
    startup_name: str,
    source_url: str,
    title: str | None = None,
    snippet: str | None = None,
) -> int:
    host = _hostname(url)
    if host in BLOCKED_ENRICHMENT_HOSTS:
        return -1

    source_host = _hostname(source_url)
    if host == source_host or host.endswith(f".{source_host}"):
        base_score = 50
        searchable_text = " ".join([url, title or "", snippet or ""])
        return base_score + (20 if _has_ai_evidence_signal(searchable_text) else 0)

    is_trusted = (
        host in TRUSTED_ENRICHMENT_HOSTS
        or host.endswith(".gupy.io")
        or host.endswith(".greenhouse.io")
        or host.endswith(".lever.co")
        or host.endswith(".linkedin.com")
    )
    if is_trusted:
        # LinkedIn (qualquer subdominio regional, ex: br.linkedin.com):
        # paginas de empresa e vagas sao uteis; perfis individuais (/in/) nao.
        if host.endswith("linkedin.com") and not any(
            segment in url.lower() for segment in ("/company/", "/jobs/")
        ):
            return -1
        searchable_text = " ".join([url, title or "", snippet or ""])
        return 90 + (20 if _has_ai_evidence_signal(searchable_text) else 0)

    terms = _startup_terms(startup_name)
    searchable_text = " ".join([url, title or "", snippet or ""])
    searchable_text_lower = searchable_text.lower()
    if terms and any(term in searchable_text_lower for term in terms):
        return 60 + (20 if _has_ai_evidence_signal(searchable_text) else 0)

    return -1


def _is_weak_source_failure(reason: str | None) -> bool:
    if not reason:
        return False

    normalized = reason.lower()
    return "rejeitado" in normalized or "mais fontes" in normalized


def _deterministic_enrichment_queries(
    *, startup_name: str, missing_signals: list[str]
) -> list[str]:
    missing_text = " ".join(missing_signals)
    return [
        f'"{startup_name}" Brasil startup artificial intelligence AI machine learning product',
        f'"{startup_name}" Brazil generative AI LLM startup {missing_text}',
        f'"{startup_name}" Brasil fundadores funding clientes',
        f'"{startup_name}" Crunchbase LinkedIn company funding Brazil',
    ]


def _unique_non_empty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


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
        task_dispatcher: UrlIngestionTaskDispatcher,
        search_planner_port: EnrichmentSearchPlannerPort | None = None,
        search_executor_port: EnrichmentSearchExecutorPort | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._scraping_port = scraping_port
        self._ingestion_port = ingestion_port
        self._embeddings_port = embeddings_port
        self._startups_port = startups_port
        self._recommendations_port = recommendations_port
        self._briefing_port = briefing_port
        self._task_dispatcher = task_dispatcher
        self._search_planner_port = search_planner_port
        self._search_executor_port = search_executor_port

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
                    reason = status.error_message or "Scraping falhou."
                    logger.warning(
                        "scraping failed, failing url ingestion job",
                        extra={"reason": reason},
                    )
                    await self._try_schedule_enrichment_after_scraping_failure(
                        job,
                        reason=reason,
                    )
                    job.fail(reason)
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

                await self._cleanup_superseded_vectors(job)

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

    async def _try_schedule_enrichment_after_scraping_failure(
        self,
        job: UrlIngestionJob,
        *,
        reason: str,
    ) -> None:
        if job.source_type != STARTUP_EVIDENCE_SOURCE_TYPE:
            return
        if job.enrichment_round >= MAX_ENRICHMENT_ROUNDS:
            return
        if not _is_weak_source_failure(reason):
            return

        try:
            if job.startup_id is None:
                startup_id = await self._startups_port.create_startup(
                    name=_derive_startup_name(title=None, url=job.url),
                    website_url=job.url,
                )
                job.link_startup(startup_id)
                await self._save(job)

            enrichment_job_ids = await self._schedule_enrichment_if_needed(
                job,
                content=None,
            )
            if enrichment_job_ids:
                logger.info(
                    "scheduled enrichment after weak source scraping failure",
                    extra={"count": len(enrichment_job_ids)},
                )
        except Exception as error:
            logger.warning(
                "failed to schedule enrichment after scraping failure",
                extra={"reason": str(error)},
            )

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

            enrichment_job_ids = await self._schedule_enrichment_if_needed(
                job,
                content=content,
            )
            if enrichment_job_ids:
                logger.info(
                    "enrichment url ingestion jobs scheduled",
                    extra={"count": len(enrichment_job_ids)},
                )

            if not job.recommendations_done:
                recommendation_count = await self._recommendations_port.generate(
                    job.startup_id
                )
                job.record_recommendations(recommendation_count)
                await self._save(job)
                logger.info(
                    "recommendations generated",
                    extra={"recommendation_count": recommendation_count},
                )
            else:
                recommendation_count = job.recommendation_count or 0
                logger.info(
                    "recommendations already done, skipping",
                    extra={"recommendation_count": recommendation_count},
                )

            briefing_id = await self._briefing_port.generate(job.startup_id)
            logger.info("briefing generated", extra={"briefing_id": str(briefing_id)})

            job.record_analysis_result(
                recommendation_count=recommendation_count, briefing_id=briefing_id
            )

    async def _schedule_enrichment_if_needed(
        self,
        job: UrlIngestionJob,
        *,
        content: DocumentContentView | None,
    ) -> list[UUID]:
        if job.startup_id is None:
            return []
        if job.enrichment_round >= MAX_ENRICHMENT_ROUNDS:
            return []

        profile = await self._startups_port.get_profile(job.startup_id)

        # Check for missing structural signals (business profile).
        basic_missing = [
            label
            for label, is_missing in (
                ("founders", not profile.founders),
                ("funding_stage", profile.funding_stage is None),
                ("customers", not profile.customers),
            )
            if is_missing
        ]

        # Also enrich when AI workload is still unknown (avoids thin-page problem).
        ai_profile_unknown = profile.ai_workload_type == "unknown"

        missing_signals = basic_missing
        if ai_profile_unknown and "ai_profile" not in missing_signals:
            missing_signals = [*missing_signals, "ai_profile"]

        if not missing_signals:
            return []

        async with self._uow_factory() as uow:
            existing_jobs = await uow.url_ingestion_job_repository.list_by_startup_id(
                job.startup_id
            )

        known_urls = {
            _normalize_url(url)
            for url in [
                job.url,
                *(profile.evidence_urls),
                *(item.url for item in existing_jobs),
            ]
            if url
        }
        same_domain_limit = (
            MAX_ENRICHMENT_URLS_PER_ROUND - 1
            if self._search_planner_port is not None
            and self._search_executor_port is not None
            else MAX_ENRICHMENT_URLS_PER_ROUND
        )
        candidates = self._same_domain_enrichment_urls(
            profile_website_url=profile.website_url,
            job_url=job.url,
            known_urls=known_urls,
            candidates=[],
        )[:same_domain_limit]

        external_candidates = await self._find_external_enrichment_urls(
            job=job,
            profile=profile,
            missing_signals=missing_signals,
            known_urls=known_urls,
            content=content,
        )
        candidates.extend(
            url
            for url in external_candidates
            if url not in known_urls and url not in candidates
        )
        candidates = candidates[:MAX_ENRICHMENT_URLS_PER_ROUND]
        if not candidates:
            return []

        created_jobs = [
            UrlIngestionJob(
                url=url,
                source_type=STARTUP_EVIDENCE_SOURCE_TYPE,
                startup_id=job.startup_id,
                parent_job_id=job.id,
                enrichment_round=job.enrichment_round + 1,
            )
            for url in candidates
        ]
        async with self._uow_factory() as uow:
            for enrichment_job in created_jobs:
                await uow.url_ingestion_job_repository.save(enrichment_job)
            await uow.commit()

        dispatched_job_ids: list[UUID] = []
        for enrichment_job in created_jobs:
            try:
                await self._task_dispatcher.dispatch(job_id=enrichment_job.id)
                dispatched_job_ids.append(enrichment_job.id)
            except Exception as error:
                logger.warning(
                    "failed to dispatch enrichment url ingestion job",
                    extra={
                        "enrichment_job_id": str(enrichment_job.id),
                        "reason": str(error),
                    },
                )

        logger.info(
            "startup profile incomplete; scheduled enrichment sources",
            extra={
                "missing_signals": missing_signals,
                "urls": [enrichment_job.url for enrichment_job in created_jobs],
            },
        )
        return dispatched_job_ids

    async def _find_external_enrichment_urls(
        self,
        *,
        job: UrlIngestionJob,
        profile: StartupProfileSnapshot,
        missing_signals: list[str],
        known_urls: set[str],
        content: DocumentContentView | None,
    ) -> list[str]:
        if self._search_planner_port is None or self._search_executor_port is None:
            return []

        known_terms = [
            term
            for term in [
                profile.name,
                *(profile.founders),
                *(profile.customers),
                profile.funding_stage,
            ]
            if term
        ]
        try:
            queries = await self._search_planner_port.plan_queries(
                startup_name=profile.name,
                source_url=job.url,
                source_title=content.title if content else None,
                raw_text=content.clean_text if content else "",
                missing_signals=missing_signals,
                known_terms=known_terms,
                excluded_urls=sorted(known_urls),
                max_queries=MAX_ENRICHMENT_SEARCH_QUERIES,
            )
        except Exception as error:
            logger.warning(
                "failed to plan enrichment searches",
                extra={"reason": str(error)},
            )
            queries = []

        queries = _unique_non_empty(
            [
                *_deterministic_enrichment_queries(
                    startup_name=profile.name,
                    missing_signals=missing_signals,
                ),
                *queries,
            ]
        )

        candidates: list[str] = []
        for query in queries:
            if len(candidates) >= MAX_ENRICHMENT_URLS_PER_ROUND:
                break
            try:
                results = await self._search_executor_port.search(
                    query,
                    excluded_urls=sorted(known_urls | set(candidates)),
                    max_results=MAX_ENRICHMENT_SEARCH_RESULTS_PER_QUERY,
                )
            except Exception as error:
                logger.warning(
                    "failed to execute enrichment search",
                    extra={"query": query, "reason": str(error)},
                )
                continue

            scored_results = sorted(
                (
                    (
                        _score_external_candidate(
                            url=_normalize_url(result.url),
                            startup_name=profile.name,
                            source_url=job.url,
                            title=result.title,
                            snippet=result.snippet,
                        ),
                        _normalize_url(result.url),
                    )
                    for result in results
                ),
                reverse=True,
            )
            for score, normalized_url in scored_results:
                if score < 0:
                    continue
                if (
                    normalized_url not in known_urls
                    and normalized_url not in candidates
                ):
                    candidates.append(normalized_url)
                if len(candidates) >= MAX_ENRICHMENT_URLS_PER_ROUND:
                    break

        return candidates

    def _same_domain_enrichment_urls(
        self,
        *,
        profile_website_url: str | None,
        job_url: str,
        known_urls: set[str],
        candidates: list[str],
    ) -> list[str]:
        return [
            url
            for url in _same_domain_candidate_urls(profile_website_url or job_url)
            if url not in known_urls and url not in candidates
        ]

    async def _cleanup_superseded_vectors(self, job: UrlIngestionJob) -> None:
        """Remove vetores Qdrant de scrapes anteriores da mesma URL.

        Re-scrape apos o cache de ``SCRAPING_RESULT_CACHE_TTL`` (scraping)
        expirar cria um ``Document`` novo para a mesma URL; sem esta
        limpeza, o ``Document`` antigo (e seus vetores no Qdrant) fica
        orfao para sempre. Best-effort: falha aqui nao impede o job atual
        de concluir, so deixa o vetor orfao pra uma limpeza futura.
        """

        async with self._uow_factory() as uow:
            previous_jobs = await uow.url_ingestion_job_repository.list_completed_by_url(
                job.url
            )

        superseded_document_ids = {
            previous.document_id
            for previous in previous_jobs
            if previous.id != job.id
            and previous.document_id is not None
            and previous.document_id != job.document_id
        }
        for document_id in superseded_document_ids:
            try:
                await self._embeddings_port.delete_vectors_for_document(document_id)
                logger.info(
                    "deleted superseded vectors from previous scrape",
                    extra={"document_id": str(document_id)},
                )
            except Exception as error:
                logger.warning(
                    "failed to delete superseded vectors",
                    extra={"document_id": str(document_id), "reason": str(error)},
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
