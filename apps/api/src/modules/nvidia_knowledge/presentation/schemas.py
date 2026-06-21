"""Schemas Pydantic do modulo NVIDIA Knowledge."""

from pydantic import BaseModel

from apps.api.src.modules.nvidia_knowledge.application.dto import (
    NvidiaTechnologyView,
)
from apps.api.src.modules.nvidia_knowledge.domain.enums import (
    NvidiaTechnologyCategory,
)


class NvidiaTechnologyResponse(BaseModel):
    slug: str
    name: str
    category: NvidiaTechnologyCategory
    description: str
    use_cases: list[str]
    keywords: list[str]
    official_url: str

    @classmethod
    def from_view(cls, view: NvidiaTechnologyView) -> "NvidiaTechnologyResponse":
        return cls(
            slug=view.slug,
            name=view.name,
            category=view.category,
            description=view.description,
            use_cases=view.use_cases,
            keywords=view.keywords,
            official_url=view.official_url,
        )
