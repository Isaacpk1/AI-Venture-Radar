"""Testes do catalogo NVIDIA Knowledge V1."""

import pytest

from apps.api.src.modules.nvidia_knowledge.application.dto import (
    ListNvidiaTechnologiesInput,
)
from apps.api.src.modules.nvidia_knowledge.application.use_cases.list_nvidia_technologies import (
    ListNvidiaTechnologies,
)
from apps.api.src.modules.nvidia_knowledge.domain.enums import (
    NvidiaTechnologyCategory,
)
from apps.api.src.modules.nvidia_knowledge.domain.exceptions import (
    NvidiaTechnologyNotFoundError,
)
from apps.api.src.modules.nvidia_knowledge.infrastructure.static_catalog.static_repository import (
    StaticNvidiaTechnologyRepository,
)


@pytest.mark.anyio
async def test_catalog_lists_initial_technologies_sorted_by_name() -> None:
    catalog = ListNvidiaTechnologies(StaticNvidiaTechnologyRepository())

    technologies = await catalog.list_technologies(ListNvidiaTechnologiesInput())

    assert len(technologies) >= 8
    assert [technology.name for technology in technologies] == sorted(
        technology.name for technology in technologies
    )
    assert all(technology.official_url.startswith("https://") for technology in technologies)


@pytest.mark.anyio
async def test_catalog_filters_by_category() -> None:
    catalog = ListNvidiaTechnologies(StaticNvidiaTechnologyRepository())

    technologies = await catalog.list_technologies(
        ListNvidiaTechnologiesInput(
            category=NvidiaTechnologyCategory.MODEL_SERVING
        )
    )

    assert technologies
    assert all(
        technology.category == NvidiaTechnologyCategory.MODEL_SERVING
        for technology in technologies
    )


@pytest.mark.anyio
async def test_catalog_searches_by_use_case_and_keywords() -> None:
    catalog = ListNvidiaTechnologies(StaticNvidiaTechnologyRepository())

    llm_matches = await catalog.list_technologies(
        ListNvidiaTechnologiesInput(query="llm")
    )
    speech_matches = await catalog.list_technologies(
        ListNvidiaTechnologiesInput(query="speech")
    )

    assert {technology.slug for technology in llm_matches} >= {
        "nvidia-nim",
        "tensorrt-llm",
    }
    assert any(technology.slug == "riva" for technology in speech_matches)


@pytest.mark.anyio
async def test_catalog_gets_technology_by_slug_case_insensitive() -> None:
    catalog = ListNvidiaTechnologies(StaticNvidiaTechnologyRepository())

    technology = await catalog.get_technology("NVIDIA-NIM")

    assert technology.slug == "nvidia-nim"
    assert technology.name == "NVIDIA NIM"


@pytest.mark.anyio
async def test_catalog_raises_when_technology_does_not_exist() -> None:
    catalog = ListNvidiaTechnologies(StaticNvidiaTechnologyRepository())

    with pytest.raises(NvidiaTechnologyNotFoundError):
        await catalog.get_technology("missing")
