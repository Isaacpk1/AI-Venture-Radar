"""Testes integrados do repositorio de url_ingestion_jobs contra PostgreSQL."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.database.relational.session import engine
from apps.api.src.modules.orchestration.domain.entities import UrlIngestionJob
from apps.api.src.modules.orchestration.domain.enums import UrlIngestionJobStatus
from apps.api.src.modules.orchestration.infrastructure.database.repositories.postgres_url_ingestion_job_repository import (
    PostgresUrlIngestionJobRepository,
)
from apps.api.src.modules.startups.domain.entities import Startup
from apps.api.src.modules.startups.infrastructure.database.repositories.postgres_startup_repository import (
    PostgresStartupRepository,
)


@pytest.mark.anyio
async def test_postgres_repository_persists_analysis_fields() -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            startup_repo = PostgresStartupRepository(session)
            startup = Startup(name="Startup Example", sector="LLM customer service")
            await startup_repo.save(startup)

            repository = PostgresUrlIngestionJobRepository(session)
            job = UrlIngestionJob(url="https://acme.example.com")
            job.start_scraping(uuid4())
            job.start_ingesting(scraping_result_id=uuid4(), ingestion_job_id=uuid4())
            job.start_embedding(document_id=uuid4(), embedding_job_id=uuid4())
            job.start_analyzing()
            await repository.save(job)

            restored = await repository.get_by_id(job.id)
            assert restored is not None
            assert restored.status is UrlIngestionJobStatus.ANALYZING
            assert restored.startup_id is None
            assert restored.evidence_attached is False

            restored.link_startup(startup.id)
            restored.mark_evidence_attached()
            briefing_id = uuid4()
            restored.record_analysis_result(
                recommendation_count=3, briefing_id=briefing_id
            )
            restored.complete()
            await repository.save(restored)

            updated = await repository.get_by_id(job.id)
            assert updated is not None
            assert updated.status is UrlIngestionJobStatus.COMPLETED
            assert updated.startup_id == startup.id
            assert updated.evidence_attached is True
            assert updated.recommendation_count == 3
            assert updated.briefing_id == briefing_id
        finally:
            await session.close()
            await transaction.rollback()

    await engine.dispose()


@pytest.mark.anyio
async def test_postgres_repository_list_page_filters_by_status_and_source_type() -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            repository = PostgresUrlIngestionJobRepository(session)

            matching = UrlIngestionJob(url="https://acme.example.com")
            matching.start_scraping(uuid4())
            other_status = UrlIngestionJob(url="https://beta.example.com")
            other_source = UrlIngestionJob(
                url="https://docs.nvidia.com/nim/", source_type="nvidia_knowledge"
            )
            other_source.start_scraping(uuid4())
            for job in (matching, other_status, other_source):
                await repository.save(job)

            jobs, total = await repository.list_page(
                page=1,
                page_size=10,
                status=UrlIngestionJobStatus.SCRAPING,
                source_type="startup_evidence",
            )

            assert total == 1
            assert jobs[0].id == matching.id
        finally:
            await session.close()
            await transaction.rollback()

    await engine.dispose()
