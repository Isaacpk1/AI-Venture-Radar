"""Rotas HTTP do modulo NVIDIA Knowledge."""

from fastapi import APIRouter, HTTPException, Query

from apps.api.src.modules.nvidia_knowledge.application.dto import (
    ListNvidiaTechnologiesInput,
)
from apps.api.src.modules.nvidia_knowledge.domain.enums import (
    NvidiaTechnologyCategory,
)
from apps.api.src.modules.nvidia_knowledge.domain.exceptions import (
    NvidiaTechnologyNotFoundError,
)
from apps.api.src.modules.nvidia_knowledge.factories.nvidia_knowledge_factory import (
    NvidiaKnowledgeFactory,
)

from .schemas import NvidiaTechnologyResponse

router = APIRouter(
    prefix="/nvidia-knowledge",
    tags=["nvidia-knowledge"],
)


@router.get("/technologies", response_model=list[NvidiaTechnologyResponse])
async def list_technologies(
    category: NvidiaTechnologyCategory | None = None,
    query: str | None = Query(default=None, min_length=1),
) -> list[NvidiaTechnologyResponse]:
    """Lista tecnologias NVIDIA do catalogo inicial."""

    catalog = NvidiaKnowledgeFactory.create_catalog()
    views = await catalog.list_technologies(
        ListNvidiaTechnologiesInput(category=category, query=query)
    )
    return [NvidiaTechnologyResponse.from_view(view) for view in views]


@router.get("/technologies/{slug}", response_model=NvidiaTechnologyResponse)
async def get_technology(slug: str) -> NvidiaTechnologyResponse:
    """Retorna uma tecnologia NVIDIA por slug."""

    catalog = NvidiaKnowledgeFactory.create_catalog()
    try:
        view = await catalog.get_technology(slug)
    except NvidiaTechnologyNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return NvidiaTechnologyResponse.from_view(view)
