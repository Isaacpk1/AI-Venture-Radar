"""Caso de uso para extrair dados estruturados de uma startup."""

from uuid import UUID

from apps.api.src.modules.startups.application.dto import (
    ExtractStartupProfileInput,
    StartupView,
)
from apps.api.src.modules.startups.application.ports import ExtractionPort
from apps.api.src.modules.startups.application.public.extraction_trigger import (
    ExtractionTrigger,
)
from apps.api.src.modules.startups.application.unit_of_work import (
    StartupsUnitOfWorkFactory,
)
from apps.api.src.modules.startups.application.use_cases.create_startup import (
    to_startup_view,
)
from apps.api.src.modules.startups.domain.exceptions import (
    StartupExtractionUnavailableError,
    StartupNotFoundError,
)


class ExtractStartupProfile(ExtractionTrigger):
    """Extrai founders/funding/customers/sector/description via Extraction Agent.

    Cada chamada repassa todas as evidencias atuais e sobrescreve
    founders/funding/customers - mesma semantica de
    ``ClassifyStartup.classify()``, sem merge incremental. sector/description
    sao exceção: ``Startup.update()`` so escreve quando o valor vem
    diferente de ``None``, e o agente devolve ``None`` quando a evidencia
    nao tem sinal suficiente para um resumo confiavel - entao um resultado
    de baixa confianca nao apaga um valor bom de uma rodada anterior.
    """

    def __init__(
        self,
        uow_factory: StartupsUnitOfWorkFactory,
        extractor: ExtractionPort | None,
    ) -> None:
        self._uow_factory = uow_factory
        self._extractor = extractor

    async def try_extract(self, startup_id: UUID) -> None:
        try:
            await self.execute(ExtractStartupProfileInput(startup_id=startup_id))
        except StartupExtractionUnavailableError:
            return

    async def execute(
        self, extract_input: ExtractStartupProfileInput
    ) -> StartupView:
        if self._extractor is None:
            raise StartupExtractionUnavailableError(
                "Servico de extracao nao configurado (verifique GEMINI_API_KEY)."
            )

        async with self._uow_factory() as uow:
            startup = await uow.startup_repository.get_by_id(
                extract_input.startup_id
            )
            if startup is None:
                raise StartupNotFoundError(
                    f"Startup {extract_input.startup_id} nao encontrada."
                )
            evidences = await uow.evidence_repository.list_by_startup_id(
                extract_input.startup_id
            )

            evidence_texts = [
                f"{evidence.title or ''} {evidence.notes or ''}".strip()
                for evidence in evidences
            ]
            outcome = await self._extractor.extract(
                name=startup.name,
                sector=startup.sector,
                description=startup.description,
                evidence_texts=[text for text in evidence_texts if text],
            )

            startup.update(
                founders=outcome.founders,
                funding_stage=outcome.funding_stage,
                funding_amount_usd=outcome.funding_amount_usd,
                customers=outcome.customers,
                sector=outcome.sector,
                description=outcome.description,
            )
            if outcome.ai_profile is not None:
                startup.update_ai_profile(outcome.ai_profile)
            await uow.startup_repository.save(startup)
            await uow.commit()

        return to_startup_view(startup)
