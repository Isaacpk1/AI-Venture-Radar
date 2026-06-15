"""Enums do dominio do modulo agents.

Este arquivo guarda apenas vocabulario generico, valido para qualquer agente
do modulo (Evidence Validation Agent, e futuramente outros). Vocabulario
especifico de um agente (ex: estados internos de um grafo) fica dentro do
proprio agente, em ``graphs/<nome_do_agente>/``.
"""

from enum import StrEnum


class AgentDecision(StrEnum):
    """Decisoes finais que qualquer agente de investigacao pode produzir.

    Este e o vocabulario INTERNO do modulo agents. O modulo scraping tem o
    seu proprio enum equivalente (``AgentInvestigationDecision``, em
    ``scraping/domain/enums.py``). A traducao entre os dois vocabularios e
    responsabilidade do adaptador
    (``scraping/infrastructure/agent_adapters/agents_semantic_investigator.py``),
    para que nenhum dos dois modulos precise importar enums do outro.
    """

    # O agente concluiu que o conteudo investigado pode ser aceito.
    ACCEPTED = "accepted"

    # O agente concluiu que o conteudo investigado deve ser rejeitado.
    REJECTED = "rejected"

    # O agente concluiu que nao ha evidencias suficientes para decidir e que
    # novas fontes precisam ser coletadas antes de uma nova tentativa.
    NEEDS_MORE_SOURCES = "needs_more_sources"
