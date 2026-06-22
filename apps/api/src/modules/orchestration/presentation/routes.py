"""Rotas HTTP do modulo orchestration."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from apps.api.src.modules.orchestration.application.dto import (
    CreateAnalysisJobInput,
)
from apps.api.src.modules.orchestration.domain.exceptions import (
    AnalysisJobNotFoundError,
    StartupProfileUnavailableError,
)
from apps.api.src.modules.orchestration.factories.orchestration_factory import (
    OrchestrationFactory,
)

from .schemas import AnalysisJobResponse, CreateAnalysisJobRequest

router = APIRouter(
    prefix="/analysis/jobs",
    tags=["orchestration"],
)


@router.post(
    "",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis_job(body: CreateAnalysisJobRequest) -> AnalysisJobResponse:
    """Executa o pipeline recommendations -> briefing para uma startup."""

    use_case = OrchestrationFactory.create_execute_analysis_job()
    try:
        view = await use_case.execute(
            CreateAnalysisJobInput(startup_id=body.startup_id)
        )
    except StartupProfileUnavailableError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return AnalysisJobResponse.from_view(view)


@router.get("/{analysis_job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(analysis_job_id: UUID) -> AnalysisJobResponse:
    """Retorna um analysis job por id."""

    use_case = OrchestrationFactory.create_get_analysis_job()
    try:
        view = await use_case.execute(analysis_job_id=analysis_job_id)
    except AnalysisJobNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return AnalysisJobResponse.from_view(view)


@router.get("", response_model=list[AnalysisJobResponse])
async def list_analysis_jobs(startup_id: UUID) -> list[AnalysisJobResponse]:
    """Lista o historico de analysis jobs de uma startup."""

    use_case = OrchestrationFactory.create_list_analysis_jobs()
    views = await use_case.execute(startup_id=startup_id)
    return [AnalysisJobResponse.from_view(view) for view in views]
