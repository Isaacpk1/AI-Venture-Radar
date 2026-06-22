"""Dispatcher inicial para UrlIngestionJob.

Enquanto o worker dedicado de Orchestration V2 nao existe, a criacao do job
mantem o estado em PostgreSQL e a API expõe um endpoint explicito de advance.
"""

from uuid import UUID

from apps.api.src.modules.orchestration.application.ports import (
    UrlIngestionTaskDispatcher,
)


class NoopUrlIngestionTaskDispatcher(UrlIngestionTaskDispatcher):
    async def dispatch(self, *, job_id: UUID) -> None:
        return None
