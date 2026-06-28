"""Politica de match determinístico entre perfil de startup e catalogo NVIDIA.

Score composto (V4, passo 3): substitui o ratio simples de keywords por uma
formula ponderada em 5 dimensoes — alinhamento de workload (35%), evidencia
concreta (25%), maturidade da startup (15%), prior de keywords (15%) e
viabilidade de implementacao (10%).

Nova confianca (V4, passo 3): combina qualidade da fonte (25%), clareza do
sinal de keywords (25%), proximidade de workload (20%), profundidade de
evidencias (20%) e sinal operacional (10%).

Nivel e faltando (V4, passo 5): cada recomendacao recebe um nivel
(forte/moderada/exploratoria) derivado do score + confianca, mais uma lista
de sinais ausentes que elevariam ao nivel superior.

Todas as funcoes sao puras, sem rede, sem banco, cobertas pela suite
existente.
"""

import re
from dataclasses import dataclass, field
from uuid import UUID

MIN_MATCHED_KEYWORDS = 2
MIN_MATCH_SCORE = 0.20
AI_NATIVE_MATURITY_BOOST = 0.05

# Limiares para classificar o nivel de cada recomendacao.
# Forte: fit claro E qualidade de evidencia boa.
# Moderada: algum sinal de relevancia E alguma evidencia de qualidade minima.
# Exploratoria: tudo abaixo, mas ainda acima do MIN_MATCH_SCORE.
NIVEL_FORTE_SCORE = 0.60
NIVEL_FORTE_CONFIDENCE = 0.55
NIVEL_MODERADA_SCORE = 0.38
NIVEL_MODERADA_CONFIDENCE = 0.25

NIVEL_FORTE = "forte"
NIVEL_MODERADA = "moderada"
NIVEL_EXPLORATORIA = "exploratoria"

# Variantes frequentes nas paginas de startups. O catalogo conserva keywords
# canonicas, enquanto a politica reconhece grafias e termos operacionais que
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

# Conversao de deployment_stage para score de maturidade (0-1).
_MATURITY_SCORE: dict[str, float] = {
    "research": 0.25,
    "mvp": 0.50,
    "pilot": 0.65,
    "production": 0.85,
    "scale": 1.00,
    "unknown": 0.50,
}

# Matriz de compatibilidade (gpu_need, tech_complexity) -> viabilidade.
_VIABILITY: dict[tuple[str, str], float] = {
    ("high",    "high"):   0.90,
    ("high",    "medium"): 0.80,
    ("high",    "low"):    0.70,
    ("medium",  "high"):   0.50,
    ("medium",  "medium"): 0.85,
    ("medium",  "low"):    0.80,
    ("low",     "high"):   0.20,
    ("low",     "medium"): 0.55,
    ("low",     "low"):    0.90,
    ("unknown", "high"):   0.50,
    ("unknown", "medium"): 0.60,
    ("unknown", "low"):    0.65,
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
class StartupAIContext:
    """Contexto de IA da startup no vocabulario deste modulo.

    Subconjunto minimo do StartupAIProfile (modulo startups) necessario para
    o score composto. A traducao e responsabilidade do adapter da camada de
    infraestrutura — policies.py nao importa nada de startups.
    """

    ai_workload_type: str = "unknown"
    deployment_stage: str = "unknown"
    gpu_need: str = "unknown"
    has_operational_signal: bool = False


@dataclass(frozen=True)
class TechnologyCandidate:
    """Tecnologia NVIDIA candidata a recomendacao, no vocabulario deste modulo."""

    slug: str
    name: str
    category: str
    use_cases: tuple[str, ...]
    keywords: tuple[str, ...]
    complexity: str = "medium"
    supported_workloads: dict[str, float] = field(default_factory=dict)


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
    signal_origins: tuple[str, ...] = field(default_factory=tuple)
    missing_signals: tuple[str, ...] = field(default_factory=tuple)
    score_breakdown: dict[str, float] = field(default_factory=dict)
    nivel: str = NIVEL_EXPLORATORIA
    faltando: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Componentes do score composto
# ---------------------------------------------------------------------------


def _workload_alignment(
    ai_context: StartupAIContext | None, candidate: TechnologyCandidate
) -> float:
    """Alinhamento entre tipo de workload da startup e perfil da tecnologia.

    Neutral (0.40) quando nao ha informacao de perfil: nem penaliza startups
    sem extracao de perfil completa, nem infla artificialmente.
    """
    if ai_context is None or not candidate.supported_workloads:
        return 0.40
    if ai_context.ai_workload_type == "unknown":
        return 0.40
    return candidate.supported_workloads.get(ai_context.ai_workload_type, 0.0)


def _evidence_signal_score(
    *,
    matched_evidence_ids: set[UUID],
    evidence_signals: list[EvidenceSignal],
) -> float:
    """Qualidade e profundidade do sinal de evidencia que suporta o match.

    Sem evidencias: 0.20 (so perfil textual, sinal fraco).
    Com evidencias: media do confidence_score + bonus de profundidade (max +0.15
    por cada evidencia adicional alem da primeira, cap em 0.95).
    """
    if not matched_evidence_ids:
        return 0.20

    matching = [s for s in evidence_signals if s.evidence_id in matched_evidence_ids]
    if not matching:
        return 0.20

    base = sum(s.confidence_score for s in matching) / len(matching)
    depth_bonus = min(0.15, 0.05 * (len(matched_evidence_ids) - 1))
    return min(0.95, base + depth_bonus)


def _startup_maturity_score(ai_context: StartupAIContext | None) -> float:
    """Score de maturidade: quanto mais proxima de producao, melhor o fit."""
    if ai_context is None:
        return 0.50
    return _MATURITY_SCORE.get(ai_context.deployment_stage, 0.50)


def _implementation_viability(
    ai_context: StartupAIContext | None, candidate: TechnologyCandidate
) -> float:
    """Compatibilidade entre necessidade de GPU da startup e complexidade da tech.

    Alta necessidade de GPU + tecnologia complexa = fit perfeito.
    Baixa necessidade + tecnologia complexa = risco real de nao conseguir
    implementar ou ver valor.
    """
    if ai_context is None:
        return 0.60
    gpu = ai_context.gpu_need
    complexity = candidate.complexity
    return _VIABILITY.get((gpu, complexity), 0.55)


def _composite_score(
    *,
    keyword_prior: float,
    workload_aln: float,
    evidence_sig: float,
    startup_mat: float,
    impl_viab: float,
    ai_maturity_level: str | None,
) -> float:
    """Score composto com 5 dimensoes ponderadas.

    ai_native recebe um bonus pequeno (5 p.p.) na dimensao de viabilidade
    de implementacao — empresas que ja constroem AI-first tem mais facilidade
    com tecnologias NVIDIA complexas. Antes o bonus era aplicado no score
    final; agora fica numa dimensao propria para nao distorcer o total.
    """
    if ai_maturity_level == "ai_native":
        impl_viab = min(1.0, impl_viab + AI_NATIVE_MATURITY_BOOST)

    return (
        0.35 * workload_aln
        + 0.25 * evidence_sig
        + 0.15 * startup_mat
        + 0.15 * keyword_prior
        + 0.10 * impl_viab
    )


def _composite_confidence(
    *,
    evidence_signals: list[EvidenceSignal],
    matched_evidence_ids: set[UUID],
    keyword_prior: float,
    workload_aln: float,
    ai_context: StartupAIContext | None,
) -> float:
    """Nova confianca: combina 5 fatores independentes.

    1. source_quality (25%): media do confidence_score das evidencias que
       contribuiram para o match; 0 quando so perfil.
    2. signal_clarity (25%): fracao de keywords do catalogo que bateram.
    3. workload_proximity (20%): reutiliza o workload_alignment.
    4. evidence_depth (20%): proporcao de evidencias independentes (cap em 3).
    5. operational_signal (10%): startup esta em producao/escala ou tem sinal
       de escala reportado.
    """
    # 1. source_quality
    if matched_evidence_ids:
        matching = [s for s in evidence_signals if s.evidence_id in matched_evidence_ids]
        source_quality = (
            sum(s.confidence_score for s in matching) / len(matching)
            if matching
            else 0.0
        )
    else:
        source_quality = 0.0

    # 2. signal_clarity = keyword_prior
    signal_clarity = keyword_prior

    # 3. workload_proximity
    workload_proximity = workload_aln

    # 4. evidence_depth: 0 evid=0.0, 1=0.33, 2=0.67, 3+=1.0
    n = len(matched_evidence_ids)
    evidence_depth = min(1.0, n / 3.0) if n > 0 else 0.0

    # 5. operational_signal
    if ai_context is not None and (
        ai_context.deployment_stage in ("production", "scale")
        or ai_context.has_operational_signal
    ):
        operational_signal = 1.0
    else:
        operational_signal = 0.0

    return (
        0.25 * source_quality
        + 0.25 * signal_clarity
        + 0.20 * workload_proximity
        + 0.20 * evidence_depth
        + 0.10 * operational_signal
    )


def _compute_nivel(score: float, confidence: float) -> str:
    """Classifica o nivel da recomendacao a partir de score e confianca.

    ``forte``      — score >= 0.60 E confidence >= 0.55: fit claro, evidencia boa.
    ``moderada``   — score >= 0.38 E confidence >= 0.25: algum sinal relevante.
    ``exploratoria`` — abaixo dos limiares, mas acima de MIN_MATCH_SCORE.
    """
    if score >= NIVEL_FORTE_SCORE and confidence >= NIVEL_FORTE_CONFIDENCE:
        return NIVEL_FORTE
    if score >= NIVEL_MODERADA_SCORE and confidence >= NIVEL_MODERADA_CONFIDENCE:
        return NIVEL_MODERADA
    return NIVEL_EXPLORATORIA


def _compute_faltando(
    *,
    nivel: str,
    score_breakdown: dict[str, float],
    confidence: float,
    missing_signals: tuple[str, ...],
    evidence_count: int,
) -> tuple[str, ...]:
    """Gera lista de sinais ausentes que elevariam ao proximo nivel.

    Para ``forte`` nada falta — lista vazia.
    Para ``moderada`` ou ``exploratoria``, aponta as dimensoes mais fracas.
    Cada item e uma string legivel em portugues, max 5 itens.
    """
    if nivel == NIVEL_FORTE:
        return ()

    items: list[str] = []

    if nivel == NIVEL_EXPLORATORIA:
        # Para subir a moderada: score >= 0.38 E confidence >= 0.25
        if score_breakdown.get("evidence_signal", 0.0) < 0.35:
            items.append("evidências concretas sobre uso da tecnologia")
        if score_breakdown.get("keyword_prior", 0.0) < 0.40 and missing_signals:
            kws = ", ".join(missing_signals[:2])
            items.append(f"sinais ausentes: {kws}")
        if score_breakdown.get("startup_maturity", 0.0) < 0.40:
            items.append("estágio de desenvolvimento declarado")
        if confidence < NIVEL_MODERADA_CONFIDENCE:
            items.append("fontes de evidência com maior confiabilidade")
        if score_breakdown.get("workload_alignment", 0.0) < 0.35:
            items.append("workload alinhado com o perfil da tecnologia")

    elif nivel == NIVEL_MODERADA:
        # Para subir a forte: score >= 0.60 E confidence >= 0.55
        if score_breakdown.get("workload_alignment", 0.0) < 0.60:
            items.append("workload da startup alinhado com a tecnologia")
        if score_breakdown.get("startup_maturity", 0.0) < 0.75:
            items.append("produto em produção ou em escala")
        if evidence_count < 2:
            items.append("mais evidências independentes sobre a tecnologia")
        elif confidence < NIVEL_FORTE_CONFIDENCE:
            items.append("evidências de maior confiabilidade")
        if missing_signals:
            kws = ", ".join(missing_signals[:2])
            items.append(f"sinais ausentes: {kws}")

    return tuple(items[:5])


def match_technologies(
    *,
    sector: str | None,
    description: str | None,
    ai_maturity_level: str | None = None,
    ai_context: StartupAIContext | None = None,
    evidence_signals: list[EvidenceSignal],
    technologies: list[TechnologyCandidate],
) -> list[MatchResult]:
    """Cruza o perfil da startup com o catalogo NVIDIA usando score composto.

    O filtro de entrada continua exigindo no minimo ``MIN_MATCHED_KEYWORDS``
    keywords (sinal minimo de relevancia) antes de computar o score composto.
    O limiar ``MIN_MATCH_SCORE`` agora e aplicado sobre o score composto (nao
    mais sobre o ratio de keywords), com valor mais baixo (0.20 vs 0.25) para
    compensar que o score composto pondera outros fatores alem de keywords.
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
        signal_origins: list[str] = []
        missing_signals: list[str] = []

        for keyword in technology.keywords:
            search_terms = (keyword, *KEYWORD_ALIASES.get(keyword, ()))
            hit_in_profile = any(
                _contains_term(profile_text, term) for term in search_terms
            )
            evidence_hits = [
                signal.evidence_id
                for signal in evidence_signals
                if any(_contains_term(signal.text, term) for term in search_terms)
            ]

            if hit_in_profile or evidence_hits:
                matched_keywords.append(keyword)
                matched_evidence_ids.update(evidence_hits)
                origin_parts: list[str] = []
                if hit_in_profile:
                    origin_parts.append("setor/descrição")
                for eid in sorted(evidence_hits, key=str):
                    origin_parts.append(f"evidência {str(eid)[:8]}")
                signal_origins.append(f"{keyword}: {', '.join(origin_parts)}")
            else:
                missing_signals.append(keyword)

        if len(matched_keywords) < MIN_MATCHED_KEYWORDS:
            continue

        keyword_prior = len(matched_keywords) / len(technology.keywords)

        workload_aln = _workload_alignment(ai_context, technology)
        evidence_sig = _evidence_signal_score(
            matched_evidence_ids=matched_evidence_ids,
            evidence_signals=evidence_signals,
        )
        startup_mat = _startup_maturity_score(ai_context)
        impl_viab = _implementation_viability(ai_context, technology)

        score = _composite_score(
            keyword_prior=keyword_prior,
            workload_aln=workload_aln,
            evidence_sig=evidence_sig,
            startup_mat=startup_mat,
            impl_viab=impl_viab,
            ai_maturity_level=ai_maturity_level,
        )

        if score < MIN_MATCH_SCORE:
            continue

        confidence = _composite_confidence(
            evidence_signals=evidence_signals,
            matched_evidence_ids=matched_evidence_ids,
            keyword_prior=keyword_prior,
            workload_aln=workload_aln,
            ai_context=ai_context,
        )

        breakdown = {
            "workload_alignment": round(workload_aln, 2),
            "evidence_signal": round(evidence_sig, 2),
            "startup_maturity": round(startup_mat, 2),
            "keyword_prior": round(keyword_prior, 2),
            "implementation_viability": round(impl_viab, 2),
        }
        nivel = _compute_nivel(score, confidence)
        missing_signals_tuple = tuple(missing_signals)
        faltando = _compute_faltando(
            nivel=nivel,
            score_breakdown=breakdown,
            confidence=round(confidence, 2),
            missing_signals=missing_signals_tuple,
            evidence_count=len(matched_evidence_ids),
        )

        results.append(
            MatchResult(
                technology=technology,
                score=round(score, 2),
                confidence=round(confidence, 2),
                matched_keywords=tuple(matched_keywords),
                evidence_ids=tuple(sorted(matched_evidence_ids, key=str)),
                signal_origins=tuple(signal_origins),
                missing_signals=missing_signals_tuple,
                score_breakdown=breakdown,
                nivel=nivel,
                faltando=faltando,
            )
        )

    results.sort(key=lambda result: result.score, reverse=True)
    return results
