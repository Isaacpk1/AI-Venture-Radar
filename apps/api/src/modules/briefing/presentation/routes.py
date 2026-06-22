"""Rotas HTTP do modulo briefing."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.api.src.modules.briefing.application.dto import GenerateBriefingInput
from apps.api.src.modules.briefing.domain.exceptions import (
    BriefingNotFoundError,
    StartupProfileUnavailableError,
)
from apps.api.src.modules.briefing.factories.briefing_factory import BriefingFactory

from .schemas import BriefingResponse, GenerateBriefingRequest

router = APIRouter(
    prefix="/briefings",
    tags=["briefing"],
)


@router.post(
    "",
    response_model=BriefingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_briefing(body: GenerateBriefingRequest) -> BriefingResponse:
    """Gera e persiste o briefing executivo mais recente de uma startup."""

    use_case = BriefingFactory.create_generate_briefing()
    try:
        view = await use_case.execute(
            GenerateBriefingInput(startup_id=body.startup_id)
        )
    except StartupProfileUnavailableError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return BriefingResponse.from_view(view)


@router.get("/{briefing_id}", response_model=BriefingResponse)
async def get_briefing(briefing_id: UUID) -> BriefingResponse:
    """Retorna um briefing por id."""

    use_case = BriefingFactory.create_get_briefing()
    try:
        view = await use_case.execute(briefing_id=briefing_id)
    except BriefingNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return BriefingResponse.from_view(view)


@router.get("", response_model=list[BriefingResponse])
async def list_briefings(startup_id: UUID) -> list[BriefingResponse]:
    """Lista briefings de uma startup."""

    use_case = BriefingFactory.create_list_briefings()
    views = await use_case.execute(startup_id=startup_id)
    return [BriefingResponse.from_view(view) for view in views]
