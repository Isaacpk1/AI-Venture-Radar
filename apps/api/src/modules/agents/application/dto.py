"""DTOs publicos do modulo agents.

Estes DTOs sao o "idioma" que outros modulos usam para falar com ``agents``.
Eles usam apenas tipos primitivos e estruturas simples (dict, list, str,
float) de proposito: assim, ``agents`` nunca precisa importar DTOs de
``scraping`` (ou de qualquer outro modulo), e ``scraping`` nunca precisa
importar enums internos de ``agents``.

Quem traduz entre os DTOs internos de ``scraping``
(``InvestigationInput``/``InvestigationResult``, em
``scraping/application/dto.py``) e estes DTOs publicos e o adaptador:
``scraping/infrastructure/agent_adapters/agents_semantic_investigator.py``.
"""

from dataclasses import dataclass, field
from uuid import UUID

from apps.api.src.modules.agents.domain.enums import (
    AgentDecision,
    AgentRunStatus,
    AgentType,
)


@dataclass(frozen=True)
class EvidenceValidationInput:
    """Contexto entregue ao Evidence Validation Agent.

    Contem o que a pipeline de scraping ja apurou: o conteudo coletado, os
    scores deterministicos e o resultado da revisao semantica simples (v7)
    que indicou a necessidade de investigacao.
    """

    url: str
    title: str | None
    raw_text: str

    # Scores deterministicos (0 a 1), calculados antes da revisao semantica.
    technical_score: float
    text_score: float
    evidence_score: float
    quality_score: float
    deterministic_problems: list[str] = field(default_factory=list)
    deterministic_warnings: list[str] = field(default_factory=list)

    # Fatores e decisao produzidos pela revisao semantica simples (v7), que
    # motivaram o acionamento do agente.
    startup_match_score: float = 0.0
    evidence_clarity_score: float = 0.0
    source_reliability_score: float = 0.0
    statement_specificity_score: float = 0.0
    context_completeness_score: float = 0.0
    contradiction_detected: bool = False
    semantic_decision: str = ""
    semantic_reason: str = ""
    semantic_confidence: float = 0.0

    # Identificador da startup investigada, quando disponivel.
    startup_id: UUID | None = None


@dataclass(frozen=True)
class EvidenceValidationResult:
    """Resultado final produzido pelo Evidence Validation Agent."""

    decision: AgentDecision
    reason: str


@dataclass(frozen=True)
class SearchPlanInput:
    """Contexto entregue ao Search Planner Agent.

    Este DTO nasce quando uma evidencia nao e suficiente e o sistema precisa
    planejar novas buscas. Ele nao cria jobs e nao chama scraper: ele apenas
    descreve o problema para o agente gerar queries.
    """

    startup_name: str | None
    source_url: str
    source_title: str | None
    raw_text: str
    reason: str
    known_terms: list[str] = field(default_factory=list)
    excluded_urls: list[str] = field(default_factory=list)
    max_queries: int = 5


@dataclass(frozen=True)
class SearchQuerySuggestion:
    """Uma query sugerida pelo Search Planner Agent."""

    query: str
    purpose: str
    priority: int


@dataclass(frozen=True)
class SearchPlanResult:
    """Plano de busca gerado pelo Search Planner Agent."""

    queries: list[SearchQuerySuggestion]
    reason: str


@dataclass(frozen=True)
class CreateAgentRunInput:
    """Entrada para criar uma execucao assincrona de agente."""

    agent_type: AgentType
    input_payload: dict[str, object]


@dataclass(frozen=True)
class AgentRunView:
    """DTO de leitura de uma execucao de agente."""

    id: UUID
    agent_type: AgentType
    status: AgentRunStatus
    input_payload: dict[str, object]
    output_payload: dict[str, object] | None
    error_message: str | None
