"""Adaptador que liga orchestration ao contrato publico do modulo recommendations.

Esta e a UNICA peca do modulo ``orchestration`` que conhece o modulo
``recommendations`` — e mesmo assim, conhece apenas o contrato publico
(``recommendations/application/public/recommendation_generator.py``). A
traducao do ``StartupProfileUnavailableError`` (vocabulario de
recommendations) para o ``StartupProfileUnavailableError`` de orchestration
acontece somente aqui.
"""

from uuid import UUID

from apps.api.src.modules.orchestration.application.ports import (
    RecommendationsPort,
)
from apps.api.src.modules.orchestration.domain.exceptions import (
    StartupProfileUnavailableError,
)
from apps.api.src.modules.recommendations.application.public.recommendation_generator import (
    RecommendationGenerator,
)
from apps.api.src.modules.recommendations.domain.exceptions import (
    StartupProfileUnavailableError as RecommendationsStartupProfileUnavailableError,
)


class RecommendationsModulePort(RecommendationsPort):
    """Implementa ``RecommendationsPort`` chamando o modulo recommendations."""

    def __init__(self, generator: RecommendationGenerator) -> None:
        self._generator = generator

    async def generate(self, startup_id: UUID) -> int:
        try:
            recommendations = await self._generator.generate(startup_id)
        except RecommendationsStartupProfileUnavailableError as error:
            raise StartupProfileUnavailableError(str(error)) from error

        return len(recommendations)
