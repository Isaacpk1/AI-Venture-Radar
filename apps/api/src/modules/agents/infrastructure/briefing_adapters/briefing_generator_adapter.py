"""Adaptador que implementa BriefingToolPort usando o contrato publico
de ``briefing``.

Nao importa nada de ``briefing`` alem de ``application/public/`` — a
instancia de ``BriefingGenerator`` e' construida pela ``BriefingFactory``
e injetada aqui.
"""

from uuid import UUID

from apps.api.src.modules.agents.application.ports import BriefingToolPort
from apps.api.src.modules.agents.domain.exceptions import AgentBriefingError
from apps.api.src.modules.briefing.application.public.briefing_generator import (
    BriefingGenerator,
)
from apps.api.src.modules.briefing.domain.exceptions import BriefingError


class BriefingGeneratorAdapter(BriefingToolPort):

    def __init__(self, generator: BriefingGenerator) -> None:
        self._generator = generator

    async def generate(self, startup_id: UUID) -> str:
        try:
            view = await self._generator.generate(startup_id)
        except BriefingError as error:
            raise AgentBriefingError(
                f"Geracao de briefing falhou: {error}"
            ) from error

        return view.content
