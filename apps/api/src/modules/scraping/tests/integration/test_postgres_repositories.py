"""Testes integrados dos repositórios contra o PostgreSQL Docker."""

from hashlib import sha256

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.database.relational.session import engine
from apps.api.src.modules.scraping.domain.entities import (
    ScrapingAttempt,
    ScrapingJob,
    ScrapingResult,
)
from apps.api.src.modules.scraping.domain.enums import (
    AttemptStatus,
    JobStatus,
    ScrapingMethod,
    ValidationDecision,
)
from apps.api.src.modules.scraping.infrastructure.database.repositories.postgres_attempt_repository import (
    PostgresScrapingAttemptRepository,
)
from apps.api.src.modules.scraping.infrastructure.database.repositories.postgres_job_repository import (
    PostgresScrapingJobRepository,
)
from apps.api.src.modules.scraping.infrastructure.database.repositories.postgres_result_repository import (
    PostgresScrapingResultRepository,
)


@pytest.mark.anyio
async def test_postgres_repositories_persist_and_restore_complete_flow() -> None:
    """Os três repositórios devem colaborar dentro da mesma transação."""

    # A conexão e a transação externas permitem fazer rollback no final. Assim,
    # o teste usa o PostgreSQL real sem deixar registros permanentes.
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            jobs = PostgresScrapingJobRepository(session)
            attempts = PostgresScrapingAttemptRepository(session)
            results = PostgresScrapingResultRepository(session)

            job = ScrapingJob(url="https://integration-test.example")
            await jobs.save(job)

            job.start()
            await jobs.save(job)

            attempt = ScrapingAttempt(
                job_id=job.id,
                method=ScrapingMethod.BEAUTIFULSOUP,
            )
            await attempts.save(attempt)
            attempt.finish_validation(
                decision=ValidationDecision.ACCEPT,
                technical_score=1.0,
                text_score=0.90,
                evidence_score=0.80,
                quality_score=0.89,
                problems=[],
                warnings=["integration_test"],
            )
            await attempts.save(attempt)

            raw_text = "Conteúdo aprovado pelo teste integrado."
            scraping_result = ScrapingResult(
                job_id=job.id,
                url=job.url,
                final_url=job.url,
                title="Teste integrado",
                raw_html=f"<html>{raw_text}</html>",
                raw_text=raw_text,
                method=ScrapingMethod.BEAUTIFULSOUP,
                status_code=200,
                technical_score=1.0,
                text_score=0.90,
                evidence_score=0.80,
                quality_score=0.89,
                content_hash=sha256(raw_text.encode("utf-8")).hexdigest(),
                metadata={"test": True},
            )
            await results.save(scraping_result)

            job.complete(scraping_result.id)
            await jobs.save(job)

            restored_job = await jobs.get_by_id(job.id)
            restored_attempts = await attempts.list_by_job_id(job.id)
            restored_result = await results.get_by_id(scraping_result.id)
            restored_by_hash = await results.get_by_content_hash(
                scraping_result.content_hash
            )

            assert restored_job is not None
            assert restored_job.status is JobStatus.COMPLETED
            assert restored_job.result_id == scraping_result.id

            assert len(restored_attempts) == 1
            assert restored_attempts[0].status is AttemptStatus.ACCEPTED
            assert restored_attempts[0].warnings == ["integration_test"]

            assert restored_result is not None
            assert restored_result.metadata == {"test": True}
            assert restored_by_hash is not None
            assert restored_by_hash.id == scraping_result.id
        finally:
            await session.close()
            await transaction.rollback()

    # O AnyIO cria loops independentes para testes distintos. Encerramos o
    # pool ainda no loop atual para nao reutilizar conexoes associadas a ele.
    await engine.dispose()
