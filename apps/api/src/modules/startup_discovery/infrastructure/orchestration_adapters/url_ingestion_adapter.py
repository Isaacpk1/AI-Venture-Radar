"""Adapter que submete URLs descobertas ao pipeline de orchestration."""

from uuid import UUID

from apps.api.src.modules.orchestration.application.dto import (
    CreateUrlIngestionJobInput,
)
from apps.api.src.modules.orchestration.application.use_cases.create_url_ingestion_job import (
    CreateUrlIngestionJob,
)


class StartupDiscoveryUrlIngestionAdapter:
    """Submete uma URL de startup descoberta como url_ingestion_job.

    source_type = "startup_evidence" para que o pipeline de analise
    (ANALYZING) seja ativado ao fim do embedding, exatamente como uma
    URL submetida manualmente pelo usuario.
    """

    def __init__(self, use_case: CreateUrlIngestionJob) -> None:
        self._use_case = use_case

    async def submit(self, url: str) -> UUID:
        view = await self._use_case.execute(
            CreateUrlIngestionJobInput(url=url, source_type="startup_evidence")
        )
        return view.id
