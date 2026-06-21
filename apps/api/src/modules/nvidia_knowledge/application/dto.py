"""DTOs do modulo NVIDIA Knowledge."""

from dataclasses import dataclass

from apps.api.src.modules.nvidia_knowledge.domain.enums import (
    NvidiaTechnologyCategory,
)


@dataclass(frozen=True)
class ListNvidiaTechnologiesInput:
    category: NvidiaTechnologyCategory | None = None
    query: str | None = None


@dataclass(frozen=True)
class NvidiaTechnologyView:
    slug: str
    name: str
    category: NvidiaTechnologyCategory
    description: str
    use_cases: list[str]
    keywords: list[str]
    official_url: str
