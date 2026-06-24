"""Testes das regras deterministicas de briefing (domain/policies.py)."""

from apps.api.src.modules.briefing.domain.policies import (
    EvidenceItem,
    RecommendationItem,
    StartupSummary,
    assess_risks,
    build_briefing_markdown,
    suggest_next_actions,
)

STARTUP = StartupSummary(
    name="Acme AI",
    sector="LLM customer service",
    description="Plataforma de atendimento com LLM.",
    country="BR",
    website_url="https://acme.example.com",
)
EVIDENCE = EvidenceItem(
    title="Acme launches LLM chatbot",
    source_url="https://example.com/news",
    evidence_type="news",
    confidence_score=0.9,
)
RECOMMENDATION = RecommendationItem(
    technology_name="NVIDIA NIM",
    category="model_serving",
    score=0.8,
    justification="Evidencias mencionam llm e inference.",
)


def test_assess_risks_flags_missing_evidence() -> None:
    risks = assess_risks([], [RECOMMENDATION])

    assert any("nenhuma evidencia" in risk.lower() for risk in risks)


def test_assess_risks_flags_missing_recommendations() -> None:
    risks = assess_risks([EVIDENCE], [])

    assert any("aderencia clara" in risk.lower() for risk in risks)


def test_assess_risks_flags_low_confidence_evidence() -> None:
    low_confidence = EvidenceItem(
        title="Vague mention",
        source_url="https://example.com/blog",
        evidence_type="blog",
        confidence_score=0.2,
    )

    risks = assess_risks([low_confidence], [RECOMMENDATION])

    assert any("confiabilidade baixa" in risk.lower() for risk in risks)


def test_assess_risks_empty_when_profile_is_solid() -> None:
    risks = assess_risks([EVIDENCE], [RECOMMENDATION])

    assert risks == []


def test_suggest_next_actions_without_recommendations() -> None:
    actions = suggest_next_actions([])

    assert any("coletar evidencias" in action.lower() for action in actions)


def test_suggest_next_actions_with_top_recommendation() -> None:
    actions = suggest_next_actions([RECOMMENDATION])

    assert actions == ["Agendar conversa tecnica sobre NVIDIA NIM (model_serving)."]


def test_build_briefing_markdown_includes_all_sections() -> None:
    content = build_briefing_markdown(
        startup=STARTUP,
        evidences=[EVIDENCE],
        recommendations=[RECOMMENDATION],
        risks=["Risco de exemplo."],
        next_actions=["Acao de exemplo."],
    )

    assert "# Briefing Executivo — Acme AI" in content
    assert "## Resumo" in content
    assert "## Evidencias Principais" in content
    assert "[Acme launches LLM chatbot](https://example.com/news)" in content
    assert "## Recomendacoes NVIDIA" in content
    assert "NVIDIA NIM" in content
    assert "## Riscos" in content
    assert "Risco de exemplo." in content
    assert "## Proximas Acoes" in content
    assert "Acao de exemplo." in content


def test_build_briefing_markdown_handles_empty_evidence_and_recommendations() -> None:
    content = build_briefing_markdown(
        startup=STARTUP,
        evidences=[],
        recommendations=[],
        risks=[],
        next_actions=["Coletar mais dados."],
    )

    assert "Nenhuma evidencia aprovada registrada." in content
    assert "Nenhuma recomendacao gerada ainda." in content
    assert "Nenhum risco identificado." in content


def test_build_briefing_markdown_includes_nvidia_context_when_provided() -> None:
    content = build_briefing_markdown(
        startup=STARTUP,
        evidences=[EVIDENCE],
        recommendations=[RECOMMENDATION],
        risks=[],
        next_actions=["Acao de exemplo."],
        nvidia_context="NVIDIA NIM e NeMo aceleram atendimento via LLM. Fontes: https://nvidia.com/nim.",
    )

    assert "## Contexto NVIDIA" in content
    assert "NVIDIA NIM e NeMo aceleram atendimento via LLM." in content
    # secao aparece entre Recomendacoes NVIDIA e Riscos, nessa ordem
    assert content.index("## Recomendacoes NVIDIA") < content.index("## Contexto NVIDIA")
    assert content.index("## Contexto NVIDIA") < content.index("## Riscos")


def test_build_briefing_markdown_omits_nvidia_context_when_absent() -> None:
    content = build_briefing_markdown(
        startup=STARTUP,
        evidences=[EVIDENCE],
        recommendations=[RECOMMENDATION],
        risks=[],
        next_actions=["Acao de exemplo."],
    )

    assert "## Contexto NVIDIA" not in content
