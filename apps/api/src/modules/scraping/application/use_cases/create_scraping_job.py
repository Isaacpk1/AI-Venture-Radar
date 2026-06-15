"""Caso de uso responsável por criar um novo job de scraping."""

from apps.api.src.modules.scraping.application.ports import TaskDispatcher
from apps.api.src.modules.scraping.application.unit_of_work import (
    ScrapingUnitOfWorkFactory,
)
from apps.api.src.modules.scraping.domain.entities import ScrapingJob
from apps.api.src.modules.scraping.domain.exceptions import TaskDispatchError


class CreateScrapingJob:
    """Cria, persiste e envia um job para execução assíncrona.

    O caso de uso coordena contratos, mas não sabe como o repositório salva os
    dados nem como o dispatcher envia a tarefa.
    """

    def __init__(
        self,
        unit_of_work_factory: ScrapingUnitOfWorkFactory,
        task_dispatcher: TaskDispatcher,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.task_dispatcher = task_dispatcher

    async def execute(self, url: str) -> ScrapingJob:
        """Cria um job pendente e envia somente seu ID para execução."""

        # A entidade nasce como pending por regra definida em ScrapingJob.
        job = ScrapingJob(url=url)

        # Primeiro persistimos o job. Assim, o futuro worker conseguirá
        # encontrá-lo quando receber o identificador pela fila.
        async with self.unit_of_work_factory() as unit_of_work:
            await unit_of_work.job_repository.save(job)
            await unit_of_work.commit()

        # Mensagens de fila devem transportar IDs, não entidades completas.
        try:
            await self.task_dispatcher.dispatch(job.id)
        except TaskDispatchError as error:
            # O job ja foi confirmado no banco. Mantemos seu historico e
            # registramos que ele falhou antes de chegar ao worker.
            job.fail_dispatch(str(error))
            async with self.unit_of_work_factory() as unit_of_work:
                await unit_of_work.job_repository.save(job)
                await unit_of_work.commit()
            raise

        return job
