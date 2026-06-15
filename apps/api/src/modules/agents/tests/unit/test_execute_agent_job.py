"""Testes do caso de uso executado pelo agent_worker."""

from uuid import uuid4

import pytest

from apps.api.src.modules.agents.application.use_cases.execute_agent_job import (
    ExecuteAgentJob,
)
@pytest.mark.anyio
async def test_execute_accepts_run_id() -> None:
    use_case = ExecuteAgentJob()

    await use_case.execute(run_id=uuid4())
