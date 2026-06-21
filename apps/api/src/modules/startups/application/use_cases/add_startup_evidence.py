"""Caso de uso para associar evidencia aprovada a uma startup."""

from apps.api.src.modules.startups.application.dto import (
    AddStartupEvidenceInput,
    StartupEvidenceView,
)
from apps.api.src.modules.startups.application.unit_of_work import (
    StartupsUnitOfWorkFactory,
)
from apps.api.src.modules.startups.domain.entities import StartupEvidence
from apps.api.src.modules.startups.domain.exceptions import StartupNotFoundError


class AddStartupEvidence:
    """Associa uma evidencia de scraping a uma startup."""

    def __init__(self, uow_factory: StartupsUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(
        self, evidence_input: AddStartupEvidenceInput
    ) -> StartupEvidenceView:
        evidence = StartupEvidence(
            startup_id=evidence_input.startup_id,
            scraping_result_id=evidence_input.scraping_result_id,
            source_url=evidence_input.source_url,
            evidence_type=evidence_input.evidence_type,
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
