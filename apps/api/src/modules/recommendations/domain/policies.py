"""Politica de match determinístico entre perfil de startup e catalogo NVIDIA.

Esta politica nao chama LLM nem agente: e regra de negocio pura, testavel sem
rede e sem banco. Quando a evidencia for ambigua demais para regras simples,
isso e trabalho de uma versao futura (Recommendations V2 - RAG, V3 - agente),
nao desta.
"""

from dataclasses import dataclass, field
from uuid import UUID

MIN_MATCHED_KEYWORDS = 1
MIN_MATCH_SCORE = 0.25


@dataclass(frozen=True)
class TechnologyCandidate:
    """Tecnologia NVIDIA candidata a recomendacao, no vocabulario deste modulo."""

    slug: str
    name: str
    category: str
    use_cases: tuple[str, ...]
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceSignal:
    """Texto pesquisavel de uma evidencia, ja normalizado em minusculas."""

    evidence_id: UUID
    text: str


@dataclass(frozen=True)
class MatchResult:
    technology: TechnologyCandidate
    score: float
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)
    evidence_ids: tuple[UUID, ...] = field(default_factory=tuple)


def match_technologies(
    *,
    sector: str | None,
    description: str | None,
    evidence_signals: list[EvidenceSignal],
    technologies: list[TechnologyCandidate],
) -> list[MatchResult]:
    """Cruza o perfil da startup com o catalogo NVIDIA por overlap de keywords.

    Uma tecnologia entra no resultado quando pelo menos ``MIN_MATCHED_KEYWORDS``
    keywords aparecem no perfil (setor/descricao) ou em alguma evidencia, e a
    fracao de keywords batidas e maior ou igual a ``MIN_MATCH_SCORE``.
    """

    profile_text = " ".join(
        part.lower() for part in (sector, description) if part
    )

    results: list[MatchResult] = []
    for technology in technologies:
        if not technology.keywords:
            continue

        matched_keywords: list[str] = []
        matched_evidence_ids: set[UUID] = set()

        for keyword in technology.keywords:
            evidence_hits = [
                signal.evidence_id
                for signal in evidence_signals
                if keyword in signal.text
            ]
            if keyword in profile_text or evidence_hits:
                matched_keywords.append(keyword)
                matched_evidence_ids.update(evidence_hits)

        score = len(matched_keywords) / len(technology.keywords)
        if len(matched_keywords) >= MIN_MATCHED_KEYWORDS and score >= MIN_MATCH_SCORE:
            results.append(
                MatchResult(
                    technology=technology,
                    score=round(score, 2),
                    matched_keywords=tuple(matched_keywords),
                    evidence_ids=tuple(
                        sorted(matched_evidence_ids, key=str)
                    ),
                )
            )

    results.sort(key=lambda result: result.score, reverse=True)
    return results
