"""Caso de uso para associar evidencia aprovada a uma startup."""

from uuid import UUID

from apps.api.src.modules.startups.application.dto import (
    AddStartupEvidenceInput,
    StartupEvidenceView,
)
from apps.api.src.modules.startups.application.public.evidence_attacher import (
    EvidenceAttacher,
)
from apps.api.src.modules.startups.application.unit_of_work import (
    StartupsUnitOfWorkFactory,
)
from apps.api.src.modules.startups.domain.entities import StartupEvidence
from apps.api.src.modules.startups.domain.enums import StartupEvidenceType
from apps.api.src.modules.startups.domain.exceptions import StartupNotFoundError

_TECHNICAL_EVIDENCE_HINTS = (
    "github.com",
    "gitlab.com",
    "docs.",
    "/docs",
    "documentation",
    "developer",
    "developers",
    "api",
    "engineering",
    "careers",
    "jobs",
    "gupy.io",
    "greenhouse.io",
    "lever.co",
    "pytorch",
    "tensorflow",
    "cuda",
    "triton",
    "vllm",
    "openai api",
    "kubernetes",
    "requirements.txt",
    "package.json",
)
_BLOG_EVIDENCE_HINTS = ("blog", "engineering")
_NEWS_EVIDENCE_HINTS = (
    "news",
    "crunchbase.com",
    "startups.com.br",
    "techcrunch.com",
    "linkedin.com/company",
)


def _infer_evidence_type(evidence_input: AddStartupEvidenceInput) -> StartupEvidenceType:
    if evidence_input.evidence_type is not StartupEvidenceType.OTHER:
        return evidence_input.evidence_type

    text = " ".join(
        [
            evidence_input.source_url,
            evidence_input.title or "",
            evidence_input.notes or "",
        ]
    ).lower()

    if any(hint in text for hint in _TECHNICAL_EVIDENCE_HINTS):
        return StartupEvidenceType.TECHNICAL
    if any(hint in text for hint in _NEWS_EVIDENCE_HINTS):
        return StartupEvidenceType.NEWS
    if any(hint in text for hint in _BLOG_EVIDENCE_HINTS):
        return StartupEvidenceType.BLOG
    if evidence_input.source_url:
        return StartupEvidenceType.WEBSITE
    return StartupEvidenceType.OTHER


class AddStartupEvidence(EvidenceAttacher):
    """Associa uma evidencia de scraping a uma startup."""

    def __init__(self, uow_factory: StartupsUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def attach_evidence(
        self,
        *,
        startup_id: UUID,
        scraping_result_id: UUID,
        source_url: str,
        title: str | None = None,
        notes: str | None = None,
    ) -> None:
        await self.execute(
            AddStartupEvidenceInput(
                startup_id=startup_id,
                scraping_result_id=scraping_result_id,
                source_url=source_url,
                title=title,
                notes=notes,
            )
        )

    async def execute(
        self, evidence_input: AddStartupEvidenceInput
    ) -> StartupEvidenceView:
        evidence = StartupEvidence(
            startup_id=evidence_input.startup_id,
            scraping_result_id=evidence_input.scraping_result_id,
            source_url=evidence_input.source_url,
            evidence_type=_infer_evidence_type(evidence_input),
            title=evidence_input.title,
            confidence_score=evidence_input.confidence_score,
            notes=evidence_input.notes,
        )

        async with self._uow_factory() as uow:
            startup = await uow.startup_repository.get_by_id(
                evidence_input.startup_id
            )
            if startup is None:
                raise StartupNotFoundError(
                    f"Startup {evidence_input.startup_id} nao encontrada."
                )
            await uow.evidence_repository.save(evidence)
            await uow.commit()

        return to_evidence_view(evidence)


def to_evidence_view(evidence: StartupEvidence) -> StartupEvidenceView:
    return StartupEvidenceView(
        id=evidence.id,
        startup_id=evidence.startup_id,
        scraping_result_id=evidence.scraping_result_id,
        source_url=evidence.source_url,
        evidence_type=evidence.evidence_type,
        title=evidence.title,
        confidence_score=evidence.confidence_score,
        notes=evidence.notes,
        created_at=evidence.created_at,
    )
