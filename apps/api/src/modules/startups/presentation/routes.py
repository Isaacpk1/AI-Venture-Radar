"""Rotas HTTP do modulo startups."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.api.src.modules.startups.application.dto import (
    AddStartupEvidenceInput,
    CreateStartupInput,
    UpdateStartupInput,
)
from apps.api.src.modules.startups.domain.exceptions import (
    InvalidStartupDataError,
    StartupNotFoundError,
)
from apps.api.src.modules.startups.factories.startups_factory import StartupsFactory

from .schemas import (
    AddStartupEvidenceRequest,
    CreateStartupRequest,
    StartupEvidenceResponse,
    StartupResponse,
    UpdateStartupRequest,
)

router = APIRouter(
    prefix="/startups",
    tags=["startups"],
)


@router.post("", response_model=StartupResponse, status_code=status.HTTP_201_CREATED)
async def create_startup(body: CreateStartupRequest) -> StartupResponse:
    """Cria uma startup."""

    use_case = StartupsFactory.create_create_startup()
    try:
        view = await use_case.execute(
            CreateStartupInput(
                name=body.name,
                website_url=body.website_url,
                description=body.description,
                sector=body.sector,
                country=body.country,
            )
        )
    except InvalidStartupDataError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return StartupResponse.from_view(view)


@router.get("/{startup_id}", response_model=StartupResponse)
async def get_startup(startup_id: UUID) -> StartupResponse:
    """Retorna uma startup."""

    use_case = StartupsFactory.create_get_startup()
    try:
        view = await use_case.execute(startup_id=startup_id)
    except StartupNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return StartupResponse.from_view(view)


@router.patch("/{startup_id}", response_model=StartupResponse)
async def update_startup(
    startup_id: UUID, body: UpdateStartupRequest
) -> StartupResponse:
    """Atualiza os campos basicos de uma startup."""

    use_case = StartupsFactory.create_update_startup()
    try:
        view = await use_case.execute(
            UpdateStartupInput(
                startup_id=startup_id,
                name=body.name,
                website_url=body.website_url,
                description=body.description,
                sector=body.sector,
                country=body.country,
            )
        )
    except StartupNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidStartupDataError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return StartupResponse.from_view(view)


@router.post(
    "/{startup_id}/evidences",
    response_model=StartupEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_startup_evidence(
    startup_id: UUID, body: AddStartupEvidenceRequest
) -> StartupEvidenceResponse:
    """Associa uma evidencia aprovada a uma startup."""

    use_case = StartupsFactory.create_add_startup_evidence()
    try:
        view = await use_case.execute(
            AddStartupEvidenceInput(
                startup_id=startup_id,
                scraping_result_id=body.scraping_result_id,
                source_url=body.source_url,
                evidence_type=body.evidence_type,
                title=body.title,
                confidence_score=body.confidence_score,
                notes=body.notes,
            )
        )
    except StartupNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidStartupDataError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return StartupEvidenceResponse.from_view(view)


@router.get(
    "/{startup_id}/evidences",
    response_model=list[StartupEvidenceResponse],
)
async def list_startup_evidences(
    startup_id: UUID,
) -> list[StartupEvidenceResponse]:
    """Lista evidencias associadas a uma startup."""

    use_case = StartupsFactory.create_list_startup_evidences()
    try:
        views = await use_case.execute(startup_id=startup_id)
    except StartupNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [StartupEvidenceResponse.from_view(view) for view in views]
