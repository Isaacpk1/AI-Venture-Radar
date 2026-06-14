"""Tarefas executadas pelo worker de scraping."""

from uuid import UUID

from apps.api.src.modules.scraping.factories.scraping_factory import ScrapingFactory


async def execute_scraping_job(job_id: str) -> None:
    """Executa um job existente usando a lógica do módulo de scraping.

    O worker recebe uma string porque filas normalmente serializam mensagens em
    formatos simples. Antes de chamar o caso de uso, convertemos o valor para o
    tipo UUID utilizado internamente.
    """

    use_case = ScrapingFactory.create_execute_scraping_job()
    await use_case.execute(UUID(job_id))
