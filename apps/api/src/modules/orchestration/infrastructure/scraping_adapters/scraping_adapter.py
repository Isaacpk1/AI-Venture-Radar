"""Adapter do modulo scraping para Orchestration V2."""

from uuid import UUID

from apps.api.src.modules.orchestration.application.ports import (
    ScrapingPort,
    StepStatus,
)
from apps.api.src.modules.scraping.application.public.job_submitter import (
    ScrapingJobSubmitter,
)


class ScrapingModulePort(ScrapingPort):
    def __init__(self, submitter: ScrapingJobSubmitter) -> None:
        self._submitter = submitter

    async def submit(self, url: str, *, source_type: str = "startup_evidence") -> UUID:
        return await self._submitter.submit(url, source_type=source_type)

    async def get_status(self, job_id: UUID) -> StepStatus:
        status = await self._submitter.get_status(job_id)
        return StepStatus(
            is_done=status.status == "completed",
            is_failed=status.status in {"failed", "cancelled"},
            result_id=status.result_id,
            error_message=status.error_message,
        )
