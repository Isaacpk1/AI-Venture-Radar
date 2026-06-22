"""Enums do modulo startups."""

from enum import Enum


class StartupEvidenceType(str, Enum):
    WEBSITE = "website"
    NEWS = "news"
    BLOG = "blog"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class AiMaturityLevel(str, Enum):
    """Classificacao de maturidade de IA produzida pelo Startup Classifier Agent.

    Vocabulario INTERNO do modulo startups. O modulo agents tem o seu
    proprio enum equivalente (``StartupMaturityLevel``, em
    ``agents/domain/enums.py``), com os mesmos valores de string. A
    traducao e responsabilidade do adaptador
    (``startups/infrastructure/agent_adapters/agents_startup_classifier.py``).
    """

    AI_NATIVE = "ai_native"
    AI_ENABLED = "ai_enabled"
    NON_AI = "non_ai"


class FundingStage(str, Enum):
    """Estagio de funding publico da startup.

    Enum fechado (nao texto livre) porque sera preenchido pelo futuro
    Extraction Agent (LLM) — garante saida estruturada validavel em vez
    de variacoes livres tipo "Series A" vs "series-a" vs "A".
    """

    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C_PLUS = "series_c_plus"
    UNKNOWN = "unknown"
