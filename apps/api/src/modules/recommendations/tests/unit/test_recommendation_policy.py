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
