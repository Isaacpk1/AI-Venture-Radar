"""Composicao das dependencias concretas do modulo startups."""

from apps.api.src.modules.startups.application.use_cases.add_startup_evidence import (
    AddStartupEvidence,
)
from apps.api.src.modules.startups.application.use_cases.create_startup import (
    CreateStartup,
)
from apps.api.src.modules.startups.application.use_cases.get_startup import GetStartup
from apps.api.src.modules.startups.application.use_cases.list_startup_evidences import (
    ListStartupEvidences,
)
from apps.api.src.modules.startups.application.use_cases.update_startup import (
    UpdateStartup,
)
from apps.api.src.modules.startups.infrastructure.database.postgres_unit_of_work import (
    PostgresStartupsUnitOfWork,
)


class StartupsFactory:
    """Ponto de composicao do modulo startups."""

    @staticmethod
    def create_create_startup() -> CreateStartup:
        return CreateStartup(PostgresStartupsUnitOfWork)

    @staticmethod
    def create_get_startup() -> GetStartup:
        return GetStartup(PostgresStartupsUnitOfWork)

    @staticmethod
    def create_update_startup() -> UpdateStartup:
        return UpdateStartup(PostgresStartupsUnitOfWork)

    @staticmethod
    def create_add_startup_evidence() -> AddStartupEvidence:
        return AddStartupEvidence(PostgresStartupsUnitOfWork)

    @staticmethod
    def create_list_startup_evidences() -> ListStartupEvidences:
        return ListStartupEvidences(PostgresStartupsUnitOfWork)
