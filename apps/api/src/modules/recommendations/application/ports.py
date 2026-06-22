"""Portas que conectam a aplicacao de recommendations a outros modulos.

``recommendations`` mantem seu proprio vocabulario (``StartupProfileSnapshot``,
``NvidiaTechnologySnapshot``). As implementacoes concretas destas portas vivem
em ``infrastructure/`` e sao o unico lugar que conhece os contratos publicos
de ``startups`` e ``nvidia_knowledge``.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from apps.api.src.modules.recommendations.application.dto import (
    NvidiaTechnologySnapshot,
    StartupProfileSnapshot,
)


class StartupProfileSource(ABC):
    """Contrato para ler o perfil de uma startup."""

    @abstractmethod
    async def get_profile(self, startup_id: UUID) -> StartupProfileSnapshot:
        """Retorna o perfil da startup ou levanta erro de dominio se ausente."""


class NvidiaCatalogSource(ABC):
    """Contrato para ler o catalogo de tecnologias NVIDIA."""

    @abstractmethod
    async def list_technologies(self) -> list[NvidiaTechnologySnapshot]:
        """Lista todas as tecnologias disponiveis para o motor de regras."""
