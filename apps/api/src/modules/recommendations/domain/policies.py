"""Politica de match determinístico entre perfil de startup e catalogo NVIDIA.

Esta politica nao chama LLM nem agente: e regra de negocio pura, testavel sem
rede e sem banco. Quando a evidencia for ambigua demais para regras simples,
isso e trabalho de uma versao futura (Recommendations V2 - RAG, V3 - agente),
nao desta.
"""

import re
from dataclasses import dataclass, field
from uuid import UUID

MIN_MATCHED_KEYWORDS = 2
MIN_MATCH_SCORE = 0.25
AI_NATIVE_SCORE_BONUS = 0.1

# Variantes frequentes nas paginas de startups. O catalogo conserva keywords
# canonic as, enquanto a politica reconhece grafias e termos operacionais que
# carregam o mesmo sinal sem depender de LLM. "scale" foi removido do alias de
# "throughput": e prefixo comum de palavras em portugues (ex. "escale") e so
# colidia por causa do match por substring que existia antes do word boundary.
KEYWORD_ALIASES: dict[str, tuple[str, ...]] = {
    "fine tuning": ("fine-tune", "fine tune", "finetune"),
    "training": ("train", "training", "retraining"),
    "model serving": ("serverless", "serving", "model deployment"),
    "inference": ("inference", "inferencing", "serving"),
    "throughput": ("throughput", "scaling"),
    "deployment": ("deployment", "deploy", "production"),
}


def _contains_term(text: str, term: str) -> bool:
    """Verifica presenca de ``term`` em ``text`` respeitando word boundary.

    Substring puro (``term in text``) gera falsos positivos linguisticos: a
    palavra em ingles "agent" bate dentro de "agentes" (portugues), "scale"
    bate dentro de "escale". ``\\b`` exige que o caracter antes/depois do termo
    nao seja alfanumerico, eliminando esses casos sem deixar de casar termos
    com espaco ou hifen internos (ex. "fine tuning", "fine-tune").
    """

    return re.search(rf"\b{re.escape(term)}\b", text) is not None


@dataclass(frozen=True)
class TechnologyCandidate:
    """Tecnologia NVIDIA candidata a recomendacao, no vocabulario deste modulo."""

    slug: str
    name: str
    category: str
    use_cases: tuple[str, ...]
    keywords: tuple[str, ...]
    complexity: str = "medium"


@dataclass(frozen=True)
class EvidenceSignal:
    """Texto pesquisavel de uma evidencia, ja normalizado em minusculas."""

    evidence_id: UUID
    text: str
    confidence_score: float = 0.5


@dataclass(frozen=True)
class MatchResult:
    technology: TechnologyCandidate
    score: float
    confidence: float = 0.0
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)
    evidence_ids: tuple[UUID, ...] = field(default_factory=tuple)


def _compute_confidence(
    *,
    score: float,
    matched_evidence_ids: set[UUID],
    evidence_signals: list[EvidenceSignal],
) -> float:
    """Calcula a confianca de uma recomendacao com base na qualidade das evidencias.

    Logica: se o match veio de evidencias reais, a media do ``confidence_score``
    delas reflete a qualidade da fonte que validou o sinal — uma pagina bem
    avaliada pelo scraper vale mais do que uma pagina de baixa qualidade.
    Se o match veio so do perfil (setor/descricao), nao temos essa validacao
    de fonte, entao a confianca e proporcional ao score, mas com teto de 0.5
    (match de texto de perfil e mais fraco que evidencia real).
    """

    if not matched_evidence_ids:
        return min(0.5, score * 0.5)

    matching_signals = [
        s for s in evidence_signals if s.evidence_id in matched_evidence_ids
    ]
    if not matching_signals:
        return min(0.5, score * 0.5)

    return sum(s.confidence_score for s in matching_signals) / len(matching_signals)


def match_technologies(
    *,
    sector: str | None,
    description: str | None,
    ai_maturity_level: str | None = None,
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
            search_terms = (keyword, *KEYWORD_ALIASES.get(keyword, ()))
            evidence_hits = [
                signal.evidence_id
                for signal in evidence_signals
                if any(_contains_term(signal.text, term) for term in search_terms)
            ]
            if (
                any(_contains_term(profile_text, term) for term in search_terms)
                or evidence_hits
            ):
                matched_keywords.append(keyword)
                matched_evidence_ids.update(evidence_hits)

        score = len(matched_keywords) / len(technology.keywords)
        if ai_maturity_level == "ai_native" and matched_keywords:
            score = min(1.0, score + AI_NATIVE_SCORE_BONUS)
        if len(matched_keywords) >= MIN_MATCHED_KEYWORDS and score >= MIN_MATCH_SCORE:
            confidence = _compute_confidence(
                score=score,
                matched_evidence_ids=matched_evidence_ids,
                evidence_signals=evidence_signals,
            )
            results.append(
                MatchResult(
                    technology=technology,
                    score=round(score, 2),
                    confidence=round(confidence, 2),
                    matched_keywords=tuple(matched_keywords),
                    evidence_ids=tuple(
                        sorted(matched_evidence_ids, key=str)
                    ),
                )
            )

    results.sort(key=lambda result: result.score, reverse=True)
    return results
