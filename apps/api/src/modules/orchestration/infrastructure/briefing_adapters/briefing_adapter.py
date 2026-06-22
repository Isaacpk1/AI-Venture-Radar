"""Adaptador que liga orchestration ao contrato publico do modulo briefing.

Esta e a UNICA peca do modulo ``orchestration`` que conhece o modulo
``briefing`` — e mesmo assim, conhece apenas o contrato publico
(``briefing/application/public/briefing_generator.py``).
"""

from uuid import UUID

from apps.api.src.modules.briefing.application.public.briefing_generator import (
    BriefingGenerator,
)
from apps.api.src.modules.briefing.domain.exceptions import (
    StartupProfileUnavailableError as BriefingStartupProfileUnavailableError,
)
from apps.api.src.modules.orchestration.application.ports import BriefingPort
from apps.api.src.modules.orchestration.domain.exceptions import (
    StartupProfileUnavailableError,
)


class BriefingModulePort(BriefingPort):
    """Implementa ``BriefingPort`` chamando o modulo briefing."""

    def __init__(self, generator: BriefingGenerator) -> None:
        self._generator = generator

    async def generate(self, startup_id: UUID) -> UUID:
        try:
            briefing = await self._generator.generate(startup_id)
        except BriefingStartupProfileUnavailableError as error:
            raise StartupProfileUnavailableError(str(error)) from error

        return briefing.id
