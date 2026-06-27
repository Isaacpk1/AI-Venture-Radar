"""Regras deterministicas de avaliacao e montagem do briefing executivo.

Riscos e proximas acoes sao inferidos por regra de codigo, nao por LLM — o
mesmo principio aplicado em ``recommendations/domain/policies.py``. Uma
versao futura com agente (Briefing V2) pode substituir/complementar isto,
nao esta.
"""

from dataclasses import dataclass

LOW_CONFIDENCE_THRESHOLD = 0.5
LOW_SCORE_THRESHOLD = 0.5


@dataclass(frozen=True)
class StartupSummary:
    name: str
    sector: str | None
    description: str | None
    country: str | None
    website_url: str | None


@dataclass(frozen=True)
class EvidenceItem:
    title: str | None
    source_url: str
    evidence_type: str
    confidence_score: float | None


@dataclass(frozen=True)
class RecommendationItem:
    technology_name: str
    category: str
    score: float
    justification: str
    confidence: float = 0.0
    complexity: str = "medium"


def assess_risks(
    evidences: list[EvidenceItem],
    recommendations: list[RecommendationItem],
) -> list[str]:
    """Aponta lacunas no perfil/recomendacoes que o leitor deveria saber."""

    risks: list[str] = []

    if not evidences:
        risks.append(
            "Nenhuma evidencia aprovada associada a esta startup; perfil "
            "pouco fundamentado."
        )
    elif any(
        evidence.confidence_score is not None
        and evidence.confidence_score < LOW_CONFIDENCE_THRESHOLD
        for evidence in evidences
    ):
        risks.append(
            "Pelo menos uma evidencia tem confiabilidade baixa "
            f"(confidence_score < {LOW_CONFIDENCE_THRESHOLD})."
        )

    if not recommendations:
        risks.append(
            "Nenhuma tecnologia NVIDIA com aderencia clara identificada com "
            "as evidencias atuais."
        )
    elif recommendations[0].score < LOW_SCORE_THRESHOLD:
        risks.append(
            "Aderencia da melhor recomendacao ainda e moderada "
            f"(score {recommendations[0].score})."
        )

    return risks


def suggest_next_actions(recommendations: list[RecommendationItem]) -> list[str]:
    """Sugere a proxima acao concreta com base na melhor recomendacao."""

    if not recommendations:
        return [
            "Coletar evidencias adicionais sobre o uso de IA da startup "
            "para habilitar recomendacoes."
        ]

    top = recommendations[0]
    if top.score < LOW_SCORE_THRESHOLD or top.confidence < LOW_CONFIDENCE_THRESHOLD:
        return [
            "Validar em conversa se ha workloads reais de GPU, inferencia, "
            "treinamento ou operacao de IA antes de propor implementacao NVIDIA."
        ]
    return [f"Agendar conversa tecnica sobre {top.technology_name} ({top.category})."]


def _recommendation_strength(recommendation: RecommendationItem) -> str:
    if recommendation.score >= 0.65 and recommendation.confidence >= 0.65:
        return "forte"
    if recommendation.score >= LOW_SCORE_THRESHOLD and recommendation.confidence >= LOW_CONFIDENCE_THRESHOLD:
        return "moderada"
    return "exploratoria"


def _best_recommendation_summary(recommendations: list[RecommendationItem]) -> str:
    if not recommendations:
        return (
            "As evidencias atuais ainda nao sustentam uma recomendacao NVIDIA "
            "prioritaria."
        )

    top = recommendations[0]
    strength = _recommendation_strength(top)
    return (
        f"Melhor sinal atual: {top.technology_name} ({strength}, "
        f"fit {top.score:.0%}, confianca {top.confidence:.0%})."
    )


def _recommendation_context(
    recommendation: RecommendationItem,
    strength: str,
) -> str:
    return (
        f"Leitura: {strength}; fit {recommendation.score:.0%}; "
        f"confianca {recommendation.confidence:.0%}; "
        f"complexidade {recommendation.complexity}."
    )


def build_briefing_markdown(
    *,
    startup: StartupSummary,
    evidences: list[EvidenceItem],
    recommendations: list[RecommendationItem],
    risks: list[str],
    next_actions: list[str],
    nvidia_context: str | None = None,
) -> str:
    """Monta o briefing executivo em Markdown a partir de dados estruturados.

    ``nvidia_context`` e' texto ja formatado (citacoes embutidas como texto
    plano) vindo de uma fundamentacao via RAG best-effort feita por quem
    chama - a funcao continua pura, sem I/O; quando ``None`` (sem
    `GEMINI_API_KEY` ou sem evidencia suficiente), a secao e' omitida.
    """

    lines = [f"# Briefing Executivo — {startup.name}", "", "## Resumo"]

    summary_parts = [part for part in (startup.sector, startup.country) if part]
    if summary_parts:
        lines.append(" | ".join(summary_parts))
    if startup.description:
        lines.append(startup.description)
    if startup.website_url:
        lines.append(f"Site: {startup.website_url}")

    lines += ["", "## Leitura Executiva"]
    lines.append(_best_recommendation_summary(recommendations))
    if recommendations and _recommendation_strength(recommendations[0]) == "exploratoria":
        lines.append(
            "A recomendacao deve ser tratada como hipotese de qualificacao, "
            "nao como indicacao tecnica fechada."
        )

    lines += ["", "## Evidencias Principais"]
    if evidences:
        for evidence in evidences:
            label = evidence.title or evidence.source_url
            lines.append(f"- [{label}]({evidence.source_url}) — {evidence.evidence_type}")
    else:
        lines.append("- Nenhuma evidencia aprovada registrada.")

    lines += ["", "## Recomendacoes NVIDIA"]
    if recommendations:
        for recommendation in recommendations:
            strength = _recommendation_strength(recommendation)
            lines.append(
                f"- **{recommendation.technology_name}** "
                f"({recommendation.category}, score {recommendation.score}) — "
                f"{_recommendation_context(recommendation, strength)} "
                f"{recommendation.justification}"
            )
    else:
        lines.append("- Nenhuma recomendacao gerada ainda.")

    if nvidia_context:
        lines += ["", "## Contexto NVIDIA", nvidia_context]

    lines += ["", "## Riscos"]
    if risks:
        lines += [f"- {risk}" for risk in risks]
    else:
        lines.append("- Nenhum risco identificado.")

    lines += ["", "## Proximas Acoes"]
    lines += [f"- {action}" for action in next_actions]

    return "\n".join(lines).strip() + "\n"
