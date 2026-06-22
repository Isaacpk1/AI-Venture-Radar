"""Caso de uso para classificar a maturidade de IA de uma startup."""

from apps.api.src.modules.startups.application.dto import (
    ClassifyStartupInput,
    StartupView,
)
from apps.api.src.modules.startups.application.ports import StartupClassifierPort
from apps.api.src.modules.startups.application.unit_of_work import (
    StartupsUnitOfWorkFactory,
)
from apps.api.src.modules.startups.application.use_cases.create_startup import (
    to_startup_view,
)
from apps.api.src.modules.startups.domain.exceptions import (
    StartupClassificationUnavailableError,
    StartupNotFoundError,
)


class ClassifyStartup:
    """Classifica uma startup chamando o Startup Classifier Agent."""

    def __init__(
        self,
        uow_factory: StartupsUnitOfWorkFactory,
        classifier: StartupClassifierPort | None,
    ) -> None:
        self._uow_factory = uow_factory
        self._classifier = classifier

    async def execute(self, classify_input: ClassifyStartupInput) -> StartupView:
        if self._classifier is None:
            raise StartupClassificationUnavailableError(
                "Servico de classificacao nao configurado (verifique GEMINI_API_KEY)."
            )

        async with self._uow_factory() as uow:
            startup = await uow.startup_repository.get_by_id(
                classify_input.startup_id
            )
            if startup is None:
                raise StartupNotFoundError(
                    f"Startup {classify_input.startup_id} nao encontrada."
                )
            evidences = await uow.evidence_repository.list_by_startup_id(
                classify_input.startup_id
            )

            evidence_texts = [
                f"{evidence.title or ''} {evidence.notes or ''}".strip()
                for evidence in evidences
            ]
            outcome = await self._classifier.classify(
                name=startup.name,
                sector=startup.sector,
                description=startup.description,
                country=startup.country,
                website_url=startup.website_url,
                evidence_texts=[text for text in evidence_texts if text],
            )

            startup.classify(outcome.level, outcome.reason)
            await uow.startup_repository.save(startup)
            await uow.commit()

        return to_startup_view(startup)
