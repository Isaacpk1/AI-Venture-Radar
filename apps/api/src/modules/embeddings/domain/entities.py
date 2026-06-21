"""Entidades e value objects do dominio do modulo embeddings."""

from dataclasses import dataclass

from apps.api.src.modules.embeddings.domain.exceptions import (
    InvalidEmbeddingDimensionError,
)


@dataclass(frozen=True)
class EmbeddingVector:
    """Vetor de embedding imutavel.

    Nao tem identidade ou ciclo de vida proprio: representa apenas o
    resultado de transformar um texto em um vetor numerico.
    """

    values: tuple[float, ...]
    dimension: int
    model_name: str

    def __post_init__(self) -> None:
        if len(self.values) != self.dimension:
            raise InvalidEmbeddingDimensionError(
                f"Vetor tem {len(self.values)} valores, "
                f"mas dimension declarada e {self.dimension}."
            )
