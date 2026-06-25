"""Caso de uso para consultar um DiscoveryRun por id."""

from typing import Callable
from uuid import UUID

from apps.api.src.modules.startup_discovery.application.dto import DiscoveryRunView
from apps.api.src.modules.startup_discovery.application.use_cases.run_discovery import (
    _to_view,
)
from apps.api.src.modules.startup_discovery.domain.exceptions import (
    DiscoveryRunNotFoundError,
)


class GetDiscoveryRun:

    def __init__(self, uow_factory: Callable) -> None:
        self._uow_factory = uow_factory

    async def execute(self, run_id: UUID) -> DiscoveryRunView:
        async with self._uow_factory() as uow:
            run = await uow.repository.get_by_id(run_id)
        if run is None:
            raise DiscoveryRunNotFoundError(f"DiscoveryRun {run_id} nao encontrado.")
        return _to_view(run, [])
