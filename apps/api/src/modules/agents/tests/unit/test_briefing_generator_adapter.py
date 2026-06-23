"""Testes do adapter BriefingGeneratorAdapter."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apps.api.src.modules.agents.domain.exceptions import AgentBriefingError
from apps.api.src.modules.agents.infrastructure.briefing_adapters.briefing_generator_adapter import (
    BriefingGeneratorAdapter,
)
from apps.api.src.modules.briefing.application.dto import BriefingView
from apps.api.src.modules.briefing.domain.exceptions import (
    StartupProfileUnavailableError,
)


class FakeBriefingGenerator:
    def __init__(self, view: BriefingView) -> None:
        self.view = view
        self.last_startup_id = None

    async def generate(self, startup_id):
        self.last_startup_id = startup_id
        return self.view


class FailingBriefingGenerator:
    async def generate(self, startup_id):
        raise StartupProfileUnavailableError("Startup nao encontrada.")


@pytest.mark.anyio
async def test_generate_returns_content() -> None:
    startup_id = uuid4()
    view = BriefingView(
        id=uuid4(),
        startup_id=startup_id,
        content="# Briefing Executivo — Acme AI\n",
        generated_at=datetime.now(UTC),
    )
    adapter = BriefingGeneratorAdapter(FakeBriefingGenerator(view))

    content = await adapter.generate(startup_id)

    assert content == "# Briefing Executivo — Acme AI\n"


@pytest.mark.anyio
async def test_generate_translates_briefing_error() -> None:
    adapter = BriefingGeneratorAdapter(FailingBriefingGenerator())

    with pytest.raises(AgentBriefingError):
        await adapter.generate(uuid4())
