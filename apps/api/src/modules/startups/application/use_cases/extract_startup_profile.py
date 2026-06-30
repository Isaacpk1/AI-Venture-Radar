"""Caso de uso para extrair dados estruturados de uma startup."""

import asyncio
from dataclasses import replace
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
from apps.api.src.modules.startups.domain.entities import StartupAIProfile
from apps.api.src.modules.startups.domain.exceptions import (
    StartupExtractionUnavailableError,
    StartupNotFoundError,
)
from apps.api.src.shared.logging import get_logger


logger = get_logger(__name__)
TRY_EXTRACT_TIMEOUT_SECONDS = 45
_AI_PROFILE_FIELD_NAMES = frozenset(
    {
        "ai_workload_type",
        "model_type",
        "data_modality",
        "deployment_stage",
        "infra_environment",
        "gpu_need",
        "latency_requirement",
        "scale_signal",
        "current_tools",
        "business_goal",
    }
)


def _profile_with_evidence_audit(
    profile: StartupAIProfile,
    *,
    all_evidence_ids: list[str],
) -> StartupAIProfile:
    if not all_evidence_ids:
        return profile

    field_evidence_ids = dict(profile.field_evidence_ids)
    for field_name in profile.field_confidence:
        if field_name not in _AI_PROFILE_FIELD_NAMES:
            continue
        if field_name in field_evidence_ids:
            continue
        value = getattr(profile, field_name, None)
        if value is None or value == ():
            continue
        if getattr(value, "value", value) == "unknown":
            continue
        field_evidence_ids[field_name] = all_evidence_ids

    if field_evidence_ids == profile.field_evidence_ids:
        return profile
    return replace(profile, field_evidence_ids=field_evidence_ids)


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
            await asyncio.wait_for(
                self.execute(ExtractStartupProfileInput(startup_id=startup_id)),
                timeout=TRY_EXTRACT_TIMEOUT_SECONDS,
            )
        except StartupExtractionUnavailableError:
            return
        except Exception as error:
            logger.warning(
                "startup extraction skipped after best-effort failure",
                extra={"startup_id": str(startup_id), "reason": str(error)},
            )
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
                (
                    f"[evidence_id={evidence.id}] "
                    f"{evidence.title or ''} {evidence.notes or ''}"
                ).strip()
                for evidence in evidences
            ]
            outcome = await self._extractor.extract(
                name=startup.name,
                sector=startup.sector,
                description=startup.description,
                evidence_texts=[text for text in evidence_texts if text],
            )

            all_evidence_ids = [str(ev.id) for ev in evidences]
            startup.update(
                founders=outcome.founders,
                funding_stage=outcome.funding_stage,
                funding_amount_usd=outcome.funding_amount_usd,
                customers=outcome.customers,
                sector=outcome.sector,
                description=outcome.description,
            )
            if outcome.ai_profile is not None:
                startup.update_ai_profile(
                    _profile_with_evidence_audit(
                        outcome.ai_profile,
                        all_evidence_ids=all_evidence_ids,
                    )
                )

            # Registra auditoria por campo: confianca do LLM + IDs das
            # evidencias que serviram de base para cada campo extraido.
            field_evidence_ids: dict[str, list[str]] = {}
            if outcome.founders:
                field_evidence_ids["founders"] = all_evidence_ids
            if outcome.funding_stage and outcome.funding_stage.value != "unknown":
                field_evidence_ids["funding_stage"] = all_evidence_ids
            if outcome.funding_amount_usd is not None:
                field_evidence_ids["funding_amount_usd"] = all_evidence_ids
            if outcome.customers:
                field_evidence_ids["customers"] = all_evidence_ids
            if outcome.sector is not None:
                field_evidence_ids["sector"] = all_evidence_ids
            if outcome.description is not None:
                field_evidence_ids["description"] = all_evidence_ids
            startup.update_field_audit(
                field_confidence=outcome.field_confidence,
                field_evidence_ids=field_evidence_ids,
            )

            await uow.startup_repository.save(startup)
            await uow.commit()

        return to_startup_view(startup)
