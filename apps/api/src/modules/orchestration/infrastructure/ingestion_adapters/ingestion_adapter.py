"""Adapter do modulo ingestion para Orchestration V2."""

from uuid import UUID

from apps.api.src.modules.ingestion.application.public.ingestion_job_submitter import (
    IngestionJobSubmitter,
)
from apps.api.src.modules.orchestration.application.ports import (
    IngestionPort,
    StepStatus,
)


class IngestionModulePort(IngestionPort):
    def __init__(self, submitter: IngestionJobSubmitter) -> None:
        self._submitter = submitter

    async def submit(
        self,
        scraping_result_id: UUID,
        *,
        source_type: str = "startup_evidence",
    ) -> UUID:
        return await self._submitter.submit(
            scraping_result_id,
            source_type=source_type,
        )

    async def get_status(self, job_id: UUID) -> StepStatus:
        status = await self._submitter.get_status(job_id)
        return StepStatus(
            is_done=status.status == "completed",
            is_failed=status.status == "failed",
            result_id=status.document_id,
            error_message=status.error_message,
        )
