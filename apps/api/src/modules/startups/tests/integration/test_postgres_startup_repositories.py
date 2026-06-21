"""Testes integrados dos repositorios de startups contra PostgreSQL."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.database.relational.session import engine
from apps.api.src.modules.startups.domain.entities import Startup, StartupEvidence
from apps.api.src.modules.startups.domain.enums import StartupEvidenceType
from apps.api.src.modules.startups.infrastructure.database.repositories.postgres_startup_evidence_repository import (
    PostgresStartupEvidenceRepository,
)
from apps.api.src.modules.startups.infrastructure.database.repositories.postgres_startup_repository import (
    PostgresStartupRepository,
)

_INSERT_SCRAPING_JOB = text("""
    INSERT INTO scraping_jobs (id, url, status, created_at)
    VALUES (:id, :url, 'completed', now())
""")

_INSERT_SCRAPING_RESULT = text("""
    INSERT INTO scraping_results (
        id, job_id, url, final_url, title, raw_html, raw_text, method,
        status_code, technical_score, text_score, evidence_score,
        quality_score, content_hash, created_at
    ) VALUES (
        :id, :job_id, :url, :url, 'Startup Example', '<html></html>', 'raw text',
        'bs4', 200, 1.0, 1.0, 1.0, 1.0, :content_hash, now()
    )
""")


@pytest.mark.anyio
async def test_postgres_startup_repositories_persist_startup_and_evidence() -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            scraping_job_id = uuid4()
            scraping_result_id = uuid4()
            await session.execute(
                _INSERT_SCRAPING_JOB,
                {"id": scraping_job_id, "url": "https://startup.example.com"},
            )
            await session.execute(
                _INSERT_SCRAPING_RESULT,
                {
                    "id": scraping_result_id,
                    "job_id": scraping_job_id,
                    "url": "https://startup.example.com",
                    "content_hash": uuid4().hex,
                },
            )
            await session.flush()

            startup_repo = PostgresStartupRepository(session)
            evidence_repo = PostgresStartupEvidenceRepository(session)

            startup = Startup(
                name="Startup Example",
                website_url="https://startup.example.com",
                sector="AI Infra",
            )
            await startup_repo.save(startup)

            evidence = StartupEvidence(
                startup_id=startup.id,
                scraping_result_id=scraping_result_id,
                source_url="https://startup.example.com",
                evidence_type=StartupEvidenceType.WEBSITE,
                confidence_score=0.95,
            )
            await evidence_repo.save(evidence)
            await session.flush()

            restored_startup = await startup_repo.get_by_id(startup.id)
            restored_evidences = await evidence_repo.list_by_startup_id(startup.id)

            assert restored_startup is not None
            assert restored_startup.name == "Startup Example"
            assert restored_startup.sector == "AI Infra"

            assert len(restored_evidences) == 1
            assert restored_evidences[0].evidence_type is StartupEvidenceType.WEBSITE
            assert restored_evidences[0].confidence_score == 0.95
        finally:
            await session.close()
            await transaction.rollback()

    await engine.dispose()
