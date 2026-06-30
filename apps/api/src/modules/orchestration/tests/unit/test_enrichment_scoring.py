"""Testes de calibracao do scoring de candidatos de enriquecimento.

Cada teste documenta um par (URL de entrada, score esperado) para garantir
que mudancas na allowlist ou na funcao de scoring nao introduzam regressoes.
"""

import pytest

from apps.api.src.modules.orchestration.application.use_cases.advance_url_ingestion_job import (
    _score_external_candidate,
)

SOURCE_URL = "https://acme.com.br"
STARTUP_NAME = "Acme Startup"


def score(url: str, title: str | None = None, snippet: str | None = None) -> int:
    return _score_external_candidate(
        url=url,
        startup_name=STARTUP_NAME,
        source_url=SOURCE_URL,
        title=title,
        snippet=snippet,
    )


# --- Bloqueados ---

@pytest.mark.parametrize(
    "url",
    [
        "https://www.facebook.com/acmestartup",
        "https://twitter.com/acme",
        "https://x.com/acme",
        "https://www.instagram.com/acme",
        "https://reddit.com/r/startups/acme",
        "https://medium.com/@acme",
        "https://quora.com/What-is-Acme",
        "https://youtube.com/watch?v=abc",
        "https://www.glassdoor.com/acme",
        "https://www.indeed.com/cmp/acme",
        "https://yelp.com/biz/acme",
        "https://wikipedia.org/wiki/acme",
    ],
)
def test_blocked_hosts_return_minus_one(url: str) -> None:
    assert score(url) == -1


# --- Trusted ---

def test_crunchbase_company_returns_90() -> None:
    assert score("https://www.crunchbase.com/organization/acme-startup") == 90


def test_linkedin_company_page_returns_90() -> None:
    assert score("https://www.linkedin.com/company/acme-startup") == 90


def test_linkedin_individual_profile_blocked() -> None:
    assert score("https://www.linkedin.com/in/joao-silva") == -1


def test_linkedin_regional_subdomain_company_page() -> None:
    assert score("https://br.linkedin.com/company/acme-startup") == 90


def test_linkedin_regional_subdomain_individual_blocked() -> None:
    assert score("https://br.linkedin.com/in/joao-silva") == -1


def test_wellfound_returns_90() -> None:
    assert score("https://wellfound.com/company/acme") == 90


def test_angel_co_returns_90() -> None:
    assert score("https://angel.co/company/acme") == 90


def test_pitchbook_returns_90() -> None:
    assert score("https://pitchbook.com/profiles/company/acme") == 90


def test_tracxn_returns_90() -> None:
    assert score("https://tracxn.com/d/companies/acme") == 90


# --- Same domain ---

def test_same_domain_returns_50() -> None:
    assert score("https://acme.com.br/about") == 50


def test_subdomain_of_source_returns_50() -> None:
    assert score("https://blog.acme.com.br/team") == 50


def test_same_domain_with_ai_signal_gets_boost() -> None:
    assert (
        score(
            "https://acme.com.br/ai",
            title="Acme AI product",
            snippet="Artificial intelligence for operations.",
        )
        == 70
    )


# --- Startup name no titulo ou snippet ---

def test_startup_name_in_title_returns_60() -> None:
    assert score("https://techcrunch.com/2025/01/acme", title="Acme Startup raises $10M") == 60


def test_startup_name_in_snippet_returns_60() -> None:
    assert score(
        "https://news.ycombinator.com/item?id=123",
        snippet="Acme Startup just launched a new product.",
    ) == 60


def test_startup_name_with_ai_signal_gets_boost() -> None:
    assert (
        score(
            "https://techcrunch.com/2025/01/acme-ai",
            title="Acme Startup launches generative AI product",
        )
        == 80
    )


# --- Desconhecido sem nome da startup ---

def test_unknown_url_without_startup_name_returns_minus_one() -> None:
    assert score("https://somesite.com/totally-unrelated-page") == -1
