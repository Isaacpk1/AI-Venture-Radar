"""Caso de uso para extrair dados estruturados de uma startup."""

import asyncio
import re
import unicodedata
from dataclasses import replace
from uuid import UUID

from apps.api.src.modules.startups.application.dto import (
    ExtractStartupProfileInput,
    StartupView,
)
from apps.api.src.modules.startups.application.ports import ExtractionOutcome, ExtractionPort
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
TRY_EXTRACT_TIMEOUT_SECONDS = 120
MAX_EVIDENCE_CHARS_FOR_EXTRACTION = 6000
MAX_BOILERPLATE_LINE_CHARS = 160
_BOILERPLATE_LINE_HINTS = (
    "assine",
    "cadastre",
    "compartilhe",
    "cookie",
    "copa do mundo fifa",
    "entrar",
    "facebook",
    "home",
    "instagram",
    "linkedin",
    "login",
    "menu",
    "newsletter",
    "politica de privacidade",
    "publicidade",
    "termos de uso",
    "twitter",
)
_CONTENT_LINE_HINTS = (
    "api",
    "bert",
    "cliente",
    "clientes",
    "computer vision",
    "funding",
    "ia",
    "inteligencia artificial",
    "machine learning",
    "modelo",
    "modelos",
    "nlp",
    "plataforma",
    "produto",
    "rodada",
    "startup",
    "treina",
    "visao computacional",
)
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
_MAIN_FIELD_NAMES = frozenset(
    {
        "founders",
        "funding_stage",
        "funding_amount_usd",
        "customers",
        "sector",
        "description",
    }
)


def _normalize_boilerplate_key(text: str) -> str:
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents).strip().lower()


def _is_boilerplate_line(line: str) -> bool:
    normalized = _normalize_boilerplate_key(line)
    if not normalized:
        return True
    if any(hint in normalized for hint in _CONTENT_LINE_HINTS):
        return False
    return len(normalized) <= MAX_BOILERPLATE_LINE_CHARS and any(
        hint in normalized for hint in _BOILERPLATE_LINE_HINTS
    )


def _strip_evidence_boilerplate(text: str) -> str:
    """Remove linhas curtas de navegacao/rodape e repeticoes obvias."""
    seen: set[str] = set()
    kept: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        key = _normalize_boilerplate_key(line)
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        if _is_boilerplate_line(line):
            continue
        kept.append(line)
    return "\n".join(kept)


def _compact_evidence_text(text: str) -> str:
    """Colapsa whitespace e limita tamanho do texto de evidencia.

    Boilerplate de navegacao infla o texto com muitos espacos e quebras de
    linha. Compactar reduz tokens sem remover palavras do corpo, e o limite por
    evidencia evita que varias paginas longas estourem o timeout do LLM.
    """
    stripped = _strip_evidence_boilerplate(text)
    compacted = re.sub(r"\s+", " ", stripped).strip()
    return compacted[:MAX_EVIDENCE_CHARS_FOR_EXTRACTION]


def _base_confidence(n_evidences: int) -> float:
    """Confidence escalada pelo numero de evidencias disponiveis."""
    if n_evidences == 0:
        return 0.35
    if n_evidences == 1:
        return 0.55
    if n_evidences == 2:
        return 0.65
    return 0.75


def _deterministic_main_field_confidence(
    outcome: ExtractionOutcome, n_evidences: int
) -> dict[str, float]:
    """Computa field_confidence para campos basicos quando o LLM retorna dict vazio.

    LLMs nao preenchem dict[str, float] com chaves livres de forma confiavel
    sob with_structured_output — este fallback garante que field_confidence
    sempre reflita o que foi extraido, mesmo sem confianca explicita do modelo.
    """
    base = _base_confidence(n_evidences)
    result: dict[str, float] = {}
    if outcome.founders:
        result["founders"] = round(base, 2)
    if outcome.funding_stage and outcome.funding_stage.value != "unknown":
        result["funding_stage"] = round(base * 0.95, 2)
    if outcome.funding_amount_usd is not None:
        result["funding_amount_usd"] = round(base * 0.85, 2)
    if outcome.customers:
        result["customers"] = round(base, 2)
    if outcome.sector is not None:
        result["sector"] = round(min(0.90, base + 0.05), 2)
    if outcome.description is not None:
        result["description"] = round(min(0.90, base + 0.05), 2)
    return result


def _deterministic_ai_profile_confidence(
    profile: StartupAIProfile, n_evidences: int
) -> dict[str, float]:
    """Computa field_confidence para o perfil de IA quando o LLM retorna dict vazio."""
    base = _base_confidence(n_evidences)
    result: dict[str, float] = {}
    for field_name in _AI_PROFILE_FIELD_NAMES:
        value = getattr(profile, field_name, None)
        if value is None or value == ():
            continue
        str_val = getattr(value, "value", value)
        if str_val == "unknown":
            continue
        result[field_name] = round(base, 2)
    return result


def _valid_field_evidence_ids(
    field_evidence_ids: dict[str, list[str]],
    *,
    allowed_fields: frozenset[str],
    known_evidence_ids: set[str],
) -> dict[str, list[str]]:
    valid: dict[str, list[str]] = {}
    for field_name, evidence_ids in field_evidence_ids.items():
        if field_name not in allowed_fields:
            continue
        filtered = [
            evidence_id
            for evidence_id in evidence_ids
            if evidence_id in known_evidence_ids
        ]
        if filtered:
            valid[field_name] = filtered
    return valid


def _profile_with_evidence_audit(
    profile: StartupAIProfile,
    *,
    all_evidence_ids: list[str],
    n_evidences: int = 0,
) -> StartupAIProfile:
    if not all_evidence_ids:
        return profile

    # Use LLM-provided confidence when available; fall back to deterministic.
    # LLMs don't reliably fill dict[str, float] under with_structured_output,
    # so field_confidence is often {} in production even when fields are extracted.
    effective_confidence = (
        profile.field_confidence
        or _deterministic_ai_profile_confidence(profile, n_evidences)
    )

    known_evidence_ids = set(all_evidence_ids)
    field_evidence_ids = _valid_field_evidence_ids(
        profile.field_evidence_ids,
        allowed_fields=_AI_PROFILE_FIELD_NAMES,
        known_evidence_ids=known_evidence_ids,
    )
    # Populate evidence_ids for every field that has a known confidence score.
    # When LLM provided specific keys, only those fields are audited (preserving
    # the agent's judgment). When using deterministic fallback, all non-unknown
    # fields get evidence_ids.
    for field_name in effective_confidence:
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

    need_replace = (
        field_evidence_ids != profile.field_evidence_ids
        or effective_confidence != profile.field_confidence
    )
    if not need_replace:
        return profile
    return replace(
        profile,
        field_evidence_ids=field_evidence_ids,
        field_confidence=effective_confidence,
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
            await asyncio.wait_for(
                self.execute(ExtractStartupProfileInput(startup_id=startup_id)),
                timeout=TRY_EXTRACT_TIMEOUT_SECONDS,
            )
        except StartupExtractionUnavailableError:
            return
        except (asyncio.TimeoutError, TimeoutError):
            logger.warning(
                "startup extraction timed out",
                extra={
                    "startup_id": str(startup_id),
                    "reason": f"timeout after {TRY_EXTRACT_TIMEOUT_SECONDS}s",
                },
            )
            return
        except Exception as error:
            logger.warning(
                "startup extraction skipped after best-effort failure",
                extra={
                    "startup_id": str(startup_id),
                    "reason": str(error) or repr(error),
                },
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
                _compact_evidence_text(
                    f"[evidence_id={evidence.id}] "
                    f"{evidence.title or ''} {evidence.notes or ''}"
                )
                for evidence in evidences
            ]
            outcome = await self._extractor.extract(
                name=startup.name,
                sector=startup.sector,
                description=startup.description,
                evidence_texts=[text for text in evidence_texts if text],
            )

            all_evidence_ids = [str(ev.id) for ev in evidences]
            known_evidence_ids = set(all_evidence_ids)
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
                        n_evidences=len(evidences),
                    )
                )

            # Registra auditoria por campo: confianca do LLM (ou fallback
            # deterministico quando o LLM retorna {}) + IDs das evidencias.
            field_evidence_ids = _valid_field_evidence_ids(
                outcome.field_evidence_ids,
                allowed_fields=_MAIN_FIELD_NAMES,
                known_evidence_ids=known_evidence_ids,
            )
            if outcome.founders:
                field_evidence_ids.setdefault("founders", all_evidence_ids)
            if outcome.funding_stage and outcome.funding_stage.value != "unknown":
                field_evidence_ids.setdefault("funding_stage", all_evidence_ids)
            if outcome.funding_amount_usd is not None:
                field_evidence_ids.setdefault("funding_amount_usd", all_evidence_ids)
            if outcome.customers:
                field_evidence_ids.setdefault("customers", all_evidence_ids)
            if outcome.sector is not None:
                field_evidence_ids.setdefault("sector", all_evidence_ids)
            if outcome.description is not None:
                field_evidence_ids.setdefault("description", all_evidence_ids)

            # field_confidence: usa o valor do LLM quando disponivel; cai para
            # calculo deterministico quando o modelo retorna dict vazio (comportamento
            # padrao observado com with_structured_output e dict[str, float] livre).
            effective_main_confidence = (
                outcome.field_confidence
                or _deterministic_main_field_confidence(outcome, len(evidences))
            )
            startup.update_field_audit(
                field_confidence=effective_main_confidence,
                field_evidence_ids=field_evidence_ids,
            )

            await uow.startup_repository.save(startup)
            await uow.commit()

        return to_startup_view(startup)
