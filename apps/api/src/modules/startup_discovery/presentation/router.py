"""Rotas HTTP do modulo startup_discovery."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from apps.api.src.modules.startup_discovery.application.dto import DiscoveryRunView
from apps.api.src.modules.startup_discovery.domain.exceptions import (
    DiscoveryRunNotFoundError,
)
from apps.api.src.modules.startup_discovery.factories.startup_discovery_factory import (
    StartupDiscoveryFactory,
)
from apps.api.src.modules.startup_discovery.presentation.schemas import (
    DiscoveryRunResponse,
    SubmittedUrlResponse,
)

router = APIRouter(prefix="/startup-discovery", tags=["startup-discovery"])


def _to_response(view: DiscoveryRunView) -> DiscoveryRunResponse:
    return DiscoveryRunResponse(
        id=view.id,
        status=view.status,
        hubs_processed=view.hubs_processed,
        urls_found=view.urls_found,
        jobs_submitted=view.jobs_submitted,
        error_message=view.error_message,
        created_at=view.created_at,
        completed_at=view.completed_at,
        submitted_urls=[
            SubmittedUrlResponse(hub_name=u.hub_name, url=u.url, job_id=u.job_id)
            for u in view.submitted_urls
        ],
    )


@router.post(
    "/runs",
    response_model=DiscoveryRunResponse,
    status_code=201,
    summary="Dispara uma rodada de descoberta de startups nos hubs cadastrados.",
)
async def run_discovery() -> DiscoveryRunResponse:
    use_case = StartupDiscoveryFactory.create_run_discovery()
    view = await use_case.execute()
    return _to_response(view)


@router.get(
    "/runs/{run_id}",
    response_model=DiscoveryRunResponse,
    summary="Retorna o resultado de uma rodada de descoberta pelo id.",
)
async def get_discovery_run(run_id: UUID) -> DiscoveryRunResponse:
    use_case = StartupDiscoveryFactory.create_get_discovery_run()
    try:
        view = await use_case.execute(run_id)
    except DiscoveryRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(view)
