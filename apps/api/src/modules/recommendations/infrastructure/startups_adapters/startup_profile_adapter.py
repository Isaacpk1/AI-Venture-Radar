"""Adaptador que liga recommendations ao contrato publico do modulo startups.

Esta e a UNICA peca do modulo ``recommendations`` que conhece o modulo
``startups`` — e mesmo assim, conhece apenas o contrato publico
(``startups/application/public/startup_profile_reader.py``). A traducao do
``StartupNotFoundError`` (vocabulario de startups) para
``StartupProfileUnavailableError`` (vocabulario de recommendations) acontece
somente aqui.
"""

from uuid import UUID

from apps.api.src.modules.recommendations.application.dto import (
    EvidenceSnapshot,
    StartupProfileSnapshot,
)
from apps.api.src.modules.recommendations.application.ports import (
    StartupProfileSource,
)
from apps.api.src.modules.recommendations.domain.exceptions import (
    StartupProfileUnavailableError,
)
from apps.api.src.modules.startups.application.public.startup_profile_reader import (
    StartupProfileReader,
)
from apps.api.src.modules.startups.domain.exceptions import StartupNotFoundError


class StartupsModuleProfileSource(StartupProfileSource):
    """Implementa ``StartupProfileSource`` chamando o modulo startups."""

    def __init__(self, reader: StartupProfileReader) -> None:
        self._reader = reader

    async def get_profile(self, startup_id: UUID) -> StartupProfileSnapshot:
        try:
            profile = await self._reader.get_profile(startup_id)
        except StartupNotFoundError as error:
            raise StartupProfileUnavailableError(str(error)) from error

        return StartupProfileSnapshot(
            sector=profile.startup.sector,
            description=profile.startup.description,
            ai_maturity_level=(
                profile.startup.ai_maturity_level.value
                if profile.startup.ai_maturity_level is not None
                else None
            ),
            evidences=tuple(
                EvidenceSnapshot(
                    evidence_id=evidence.id,
                    title=evidence.title,
                    notes=evidence.notes,
                )
                for evidence in profile.evidences
            ),
        )
