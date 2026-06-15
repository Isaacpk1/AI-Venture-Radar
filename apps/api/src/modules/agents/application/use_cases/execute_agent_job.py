"""Caso de uso executado pelo agent_worker.

Esta V3.5 cria a base operacional do worker. A fila transporta somente
``run_id``; os detalhes da execucao devem ficar no futuro registro
``agent_runs`` no PostgreSQL.
"""

from uuid import UUID

class ExecuteAgentJob:
    """Executa uma tarefa de agente recebida pela fila."""

    async def execute(
        self,
        *,
        run_id: UUID,
    ) -> None:
        """Prepara o ponto de extensao para execucao assincorna.

        A proxima versao carregara ``agent_runs`` pelo ``run_id``. Com isso, o
        worker nao precisara receber payload grande nem conhecer detalhes do
        agente pela mensagem da fila.
        """

        # Na proxima versao, este ponto carregara o AgentRun do banco e
        # executara o grafo adequado.
        _ = run_id
