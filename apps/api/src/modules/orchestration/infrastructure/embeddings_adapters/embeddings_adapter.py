"""Adapter do modulo embeddings para Orchestration V2."""

from uuid import UUID

from apps.api.src.modules.embeddings.application.public.embedding_job_submitter import (
    EmbeddingJobSubmitter,
)
from apps.api.src.modules.orchestration.application.ports import (
    EmbeddingsPort,
    StepStatus,
)


class EmbeddingsModulePort(EmbeddingsPort):
    def __init__(self, submitter: EmbeddingJobSubmitter) -> None:
        self._submitter = submitter

    async def submit(self, document_id: UUID) -> UUID:
        return await self._submitter.submit(document_id)

    async def get_status(self, job_id: UUID) -> StepStatus:
        status = await self._submitter.get_status(job_id)
        return StepStatus(
            is_done=status.status in {"completed", "partial"},
            is_failed=status.status == "failed",
            result_id=None,
            error_message=status.error_message,
        )
