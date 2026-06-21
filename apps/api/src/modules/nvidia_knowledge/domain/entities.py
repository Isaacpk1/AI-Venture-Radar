"""Entidades do dominio do modulo NVIDIA Knowledge."""

from dataclasses import dataclass

from apps.api.src.modules.nvidia_knowledge.domain.enums import (
    NvidiaTechnologyCategory,
)


def _normalize_slug(value: str) -> str:
    return value.strip().lower()


@dataclass(frozen=True)
class NvidiaTechnology:
    """Tecnologia NVIDIA disponivel para recomendacao futura."""

    slug: str
    name: str
    category: NvidiaTechnologyCategory
    description: str
    use_cases: tuple[str, ...]
    keywords: tuple[str, ...]
    official_url: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "slug", _normalize_slug(self.slug))
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(
            self,
            "use_cases",
            tuple(item.strip() for item in self.use_cases if item.strip()),
        )
        object.__setattr__(
            self,
            "keywords",
            tuple(item.strip().lower() for item in self.keywords if item.strip()),
        )
        object.__setattr__(self, "official_url", self.official_url.strip())

        if not self.slug:
            raise ValueError("Tecnologia NVIDIA precisa ter slug.")
        if not self.name:
            raise ValueError("Tecnologia NVIDIA precisa ter nome.")
        if not self.description:
            raise ValueError("Tecnologia NVIDIA precisa ter descricao.")
        if not self.use_cases:
            raise ValueError("Tecnologia NVIDIA precisa ter casos de uso.")
        if not self.official_url:
            raise ValueError("Tecnologia NVIDIA precisa ter fonte oficial.")

    def matches_query(self, query: str) -> bool:
        """Retorna True quando a query aparece em campos pesquisaveis."""

        normalized_query = query.strip().lower()
        if not normalized_query:
            return True

        searchable_text = " ".join(
            [
                self.slug,
                self.name.lower(),
                self.category.value,
                self.description.lower(),
                " ".join(self.use_cases).lower(),
                " ".join(self.keywords),
            ]
        )
        return normalized_query in searchable_text
