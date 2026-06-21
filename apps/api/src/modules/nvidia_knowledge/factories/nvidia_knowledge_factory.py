"""Composicao das dependencias concretas do modulo NVIDIA Knowledge."""

from apps.api.src.modules.nvidia_knowledge.application.use_cases.list_nvidia_technologies import (
    ListNvidiaTechnologies,
)
from apps.api.src.modules.nvidia_knowledge.infrastructure.static_catalog.static_repository import (
    StaticNvidiaTechnologyRepository,
)


class NvidiaKnowledgeFactory:
    """Ponto de composicao do modulo NVIDIA Knowledge."""

    @staticmethod
    def create_catalog() -> ListNvidiaTechnologies:
        return ListNvidiaTechnologies(StaticNvidiaTechnologyRepository())
