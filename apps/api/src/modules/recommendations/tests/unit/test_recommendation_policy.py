"""Testes da politica de match determinístico (domain/policies.py).

Os cenarios espelham o mapeamento de tecnologias NVIDIA documentado no
CLAUDE.md (ex: "LLMs in customer service -> NIM, NeMo, TensorRT-LLM").
"""

from uuid import uuid4

from apps.api.src.modules.recommendations.domain.policies import (
    EvidenceSignal,
    TechnologyCandidate,
    match_technologies,
)

NIM = TechnologyCandidate(
    slug="nvidia-nim",
    name="NVIDIA NIM",
    category="model_serving",
    use_cases=("servir LLMs e modelos generativos em producao",),
    keywords=("llm", "generative ai", "inference", "api", "deployment", "microservice"),
)
NEMO = TechnologyCandidate(
    slug="nvidia-nemo",
    name="NVIDIA NeMo",
    category="model_training",
    use_cases=("fine-tuning de modelos generativos",),
    keywords=("training", "fine tuning", "llm", "agent", "generative ai", "speech"),
)
RIVA = TechnologyCandidate(
    slug="riva",
    name="NVIDIA Riva",
    category="speech_ai",
    use_cases=("automatic speech recognition",),
    keywords=("speech", "asr", "tts", "voice", "translation", "conversational ai"),
)
MONAI = TechnologyCandidate(
    slug="monai",
    name="MONAI",
    category="healthcare_ai",
    use_cases=("analise de imagens medicas",),
    keywords=("healthcare", "medical imaging", "monai", "segmentation", "radiology", "clinical ai"),
)
RAPIDS = TechnologyCandidate(
    slug="rapids",
    name="RAPIDS",
    category="data_science",
    use_cases=("acelerar pipelines de data science",),
    keywords=("data science", "analytics", "dataframe", "gpu", "pandas", "spark"),
)
CATALOG = [NIM, NEMO, RIVA, MONAI, RAPIDS]


def test_llm_customer_service_profile_matches_nim_and_nemo() -> None:
    results = match_technologies(
        sector="LLM and generative AI",
        description=(
            "Provides inference API with simple deployment as microservice "
            "architecture."
        ),
        evidence_signals=[],
        technologies=CATALOG,
    )

    slugs = [result.technology.slug for result in results]
    assert "nvidia-nim" in slugs
    assert "nvidia-nemo" in slugs
    assert "riva" not in slugs
    assert "monai" not in slugs

    nim_result = next(result for result in results if result.technology.slug == "nvidia-nim")
    assert nim_result.score == 1.0
    assert set(nim_result.matched_keywords) == set(NIM.keywords)


def test_healthcare_profile_matches_monai_only() -> None:
    results = match_technologies(
        sector="Healthcare AI for medical imaging",
        description=(
            "Clinical AI platform for radiology segmentation using MONAI."
        ),
        evidence_signals=[],
        technologies=CATALOG,
    )

    slugs = [result.technology.slug for result in results]
    assert slugs == ["monai"]
    assert results[0].score == 1.0


def test_voice_profile_matches_riva_only() -> None:
    results = match_technologies(
        sector="Voice AI startup",
        description=(
            "Provides automatic speech recognition (asr), text-to-speech "
            "(tts), and voice translation for conversational ai assistants."
        ),
        evidence_signals=[],
        technologies=CATALOG,
    )

    slugs = [result.technology.slug for result in results]
    assert slugs == ["riva"]
    assert results[0].score == 1.0


def test_profile_without_ai_evidence_returns_no_matches() -> None:
    results = match_technologies(
        sector="Traditional retail",
        description="Sells shoes in physical stores.",
        evidence_signals=[],
        technologies=CATALOG,
    )

    assert results == []


def test_match_found_only_in_evidence_text_is_traceable() -> None:
    evidence_id = uuid4()
    results = match_technologies(
        sector=None,
        description=None,
        evidence_signals=[
            EvidenceSignal(
                evidence_id=evidence_id,
                text="our new generative ai inference api deployment as a microservice",
            )
        ],
        technologies=CATALOG,
    )

    assert len(results) == 1
    assert results[0].technology.slug == "nvidia-nim"
    assert results[0].evidence_ids == (evidence_id,)


def test_results_are_sorted_by_score_descending() -> None:
    results = match_technologies(
        sector="LLM and generative AI",
        description="Provides inference API with simple deployment as microservice.",
        evidence_signals=[],
        technologies=CATALOG,
    )

    scores = [result.score for result in results]
    assert scores == sorted(scores, reverse=True)


def test_operational_aliases_match_ai_infrastructure_signals() -> None:
    results = match_technologies(
        sector="AI infrastructure",
        description="",
        evidence_signals=[
            EvidenceSignal(
                evidence_id=uuid4(),
                text="train fine-tune and deploy serverless inference workloads at scale",
            )
        ],
        technologies=CATALOG,
    )

    slugs = [result.technology.slug for result in results]
    assert "nvidia-nim" in slugs
    assert "nvidia-nemo" in slugs


def test_ai_native_bonus_can_promote_a_candidate_with_enough_signals() -> None:
    results = match_technologies(
        sector=None,
        description=None,
        ai_maturity_level="ai_native",
        evidence_signals=[
            EvidenceSignal(evidence_id=uuid4(), text="fine-tune llm models")
        ],
        technologies=[NEMO],
    )

    assert results[0].technology.slug == "nvidia-nemo"
    assert results[0].score == 0.43


def test_single_generic_keyword_is_not_enough_for_recommendation() -> None:
    results = match_technologies(
        sector=None,
        description=None,
        ai_maturity_level="ai_native",
        evidence_signals=[EvidenceSignal(evidence_id=uuid4(), text="platform")],
        technologies=[
            TechnologyCandidate(
                slug="nvidia-ai-enterprise",
                name="NVIDIA AI Enterprise",
                category="ai_platform",
                use_cases=("padronizar stack corporativa de IA",),
                keywords=(
                    "enterprise",
                    "platform",
                    "governance",
                    "deployment",
                    "support",
                    "infrastructure",
                ),
            )
        ],
    )

    assert results == []


def test_word_boundary_avoids_cross_language_false_positives() -> None:
    """Reproduz o bug real encontrado com https://dadosfera.com.br: o texto
    raspado em portugues continha "agentes"/"agente de ia" e "escale com ia",
    que batiam por substring puro nas keywords em ingles "agent" e no alias
    "scale" de "throughput" sem nenhuma relacao semantica real.
    """

    results = match_technologies(
        sector=None,
        description=None,
        evidence_signals=[
            EvidenceSignal(
                evidence_id=uuid4(),
                text=(
                    "seu proprio agente de ia interpreta perguntas. agentes "
                    "autonomos com acesso a base de conhecimento. organize, "
                    "otimize e escale com ia."
                ),
            )
        ],
        technologies=CATALOG,
    )

    assert results == []


def test_word_boundary_still_matches_real_standalone_keywords() -> None:
    evidence_id = uuid4()
    results = match_technologies(
        sector=None,
        description=None,
        evidence_signals=[
            EvidenceSignal(
                evidence_id=evidence_id,
                text="we are building an llm-based ai agent platform for enterprise teams",
            )
        ],
        technologies=[NEMO],
    )

    assert len(results) == 1
    assert results[0].technology.slug == "nvidia-nemo"
    assert "agent" in results[0].matched_keywords
    assert "llm" in results[0].matched_keywords


def test_confidence_reflects_evidence_quality() -> None:
    """Match com evidencia de alta qualidade gera confianca mais alta."""

    high_conf_id = uuid4()
    results = match_technologies(
        sector=None,
        description=None,
        evidence_signals=[
            EvidenceSignal(
                evidence_id=high_conf_id,
                text="generative ai inference api deployment microservice",
                confidence_score=0.9,
            )
        ],
        technologies=[NIM],
    )

    assert len(results) == 1
    assert results[0].confidence == 0.9


def test_confidence_is_lower_for_profile_only_match() -> None:
    """Match que veio so do perfil (setor/descricao) recebe confianca reduzida."""

    results = match_technologies(
        sector="LLM and generative AI inference API deployment microservice",
        description=None,
        evidence_signals=[],
        technologies=[NIM],
    )

    assert len(results) == 1
    # Score 1.0 -> confianca = min(0.5, 1.0 * 0.5) = 0.5
    assert results[0].confidence == 0.5
    assert results[0].confidence < results[0].score


def test_confidence_averages_multiple_evidence_quality_scores() -> None:
    """Confianca e' a media dos confidence_scores das evidencias que matcharam."""

    id1, id2 = uuid4(), uuid4()
    results = match_technologies(
        sector=None,
        description=None,
        evidence_signals=[
            EvidenceSignal(evidence_id=id1, text="llm inference api deployment microservice", confidence_score=0.8),
            EvidenceSignal(evidence_id=id2, text="generative ai deployment", confidence_score=0.4),
        ],
        technologies=[NIM],
    )

    assert len(results) == 1
    # Ambas as evidencias matcham, media = (0.8 + 0.4) / 2 = 0.6
    assert results[0].confidence == 0.6


def test_complexity_propagated_from_candidate() -> None:
    """complexity do TechnologyCandidate aparece no MatchResult via TechnologyCandidate."""

    nim_low = TechnologyCandidate(
        slug="nvidia-nim",
        name="NVIDIA NIM",
        category="model_serving",
        use_cases=("servir LLMs",),
        keywords=("llm", "inference"),
        complexity="low",
    )
    results = match_technologies(
        sector="llm inference",
        description=None,
        evidence_signals=[],
        technologies=[nim_low],
    )

    assert len(results) == 1
    assert results[0].technology.complexity == "low"
