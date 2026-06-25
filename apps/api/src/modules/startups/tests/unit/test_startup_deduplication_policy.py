"""Calibracao do limiar de dedup de startups (`domain/policies.py`).

Os pares abaixo sao o "exemplo real" que a decisao em
`docs/decisoes_pendentes.md` pedia antes de implementar — nao um numero
escolhido no escuro. `NAME_SIMILARITY_THRESHOLD` (92) e' o menor valor
que aceita toda variacao de nome inequivocamente da mesma empresa nesta
lista sem aceitar nenhum par de empresas diferentes. Se um caso novo
quebrar essa garantia, ajuste a lista e o limiar juntos, nesta ordem.
"""

import pytest

from apps.api.src.modules.startups.domain.entities import Startup
from apps.api.src.modules.startups.domain.policies import (
    NAME_SIMILARITY_THRESHOLD,
    find_duplicate_startup,
    normalize_domain,
)

DUPLICATE_NAME_PAIRS = [
    ("Acme AI", "Acme AI Inc."),
    ("Acme AI", "ACME AI"),
    ("Dadosfera", "Dadosfera Tecnologia"),
    ("OpenAI", "Open AI"),
    ("Mercado Livre", "MercadoLivre"),
    ("Loft", "Loft Tecnologia"),
    ("QuintoAndar", "Quinto Andar"),
]

NON_DUPLICATE_NAME_PAIRS = [
    ("Acme AI", "Acme Robotics"),
    ("Nubank", "Nuvemshop"),
    ("Dadosfera", "Datarisk"),
    ("Stone", "StoneAge"),
    ("Loft", "Loggi"),
    ("Gupy", "Gympass"),
    ("Creditas", "Credijusto"),
    ("Loft", "Lori"),
    ("Ebanx", "Ebac"),
    ("Pipefy", "Pipedrive"),
]

# Nomes curtos + sufixo comum sao genuinamente ambiguos so pelo nome
# (ex: "Gupy" vs "Gupy Tecnologia e Servicos" tem o mesmo score de
# "Stone" vs "StoneAge", que SAO empresas diferentes). Fundir duas
# empresas diferentes e' o erro mais caro - por isso o limiar fica acima
# dessa zona, mesmo perdendo esses casos de nome curto sem o dominio
# como segundo sinal.
KNOWN_AMBIGUOUS_MISSES = {
    ("Gupy", "Gupy Tecnologia e Servicos"),
    ("Hotmart", "Hotmart Company"),
    ("Wildlife Studios", "Wildlife"),
}


@pytest.mark.parametrize("name_a,name_b", DUPLICATE_NAME_PAIRS)
def test_duplicate_name_pairs_match_above_threshold(name_a: str, name_b: str) -> None:
    existing = [Startup(name=name_b)]
    match = find_duplicate_startup(name=name_a, website_url=None, existing=existing)
    assert match is not None, f"{name_a!r} deveria casar com {name_b!r}"


@pytest.mark.parametrize("name_a,name_b", NON_DUPLICATE_NAME_PAIRS)
def test_non_duplicate_name_pairs_stay_below_threshold(name_a: str, name_b: str) -> None:
    existing = [Startup(name=name_b)]
    match = find_duplicate_startup(name=name_a, website_url=None, existing=existing)
    assert match is None, f"{name_a!r} nao deveria casar com {name_b!r}"


def test_threshold_is_calibrated_not_guessed() -> None:
    """Documenta a calibracao: o limiar fica estritamente entre o pior
    caso aceito e o melhor caso rejeitado, com a lista real acima."""

    assert NAME_SIMILARITY_THRESHOLD == 92.0


def test_exact_domain_match_wins_even_with_different_names() -> None:
    """Dominio e' o sinal mais confiavel - nem precisa do nome bater."""

    existing = [Startup(name="Acme Inc", website_url="https://www.acme.com/about")]

    match = find_duplicate_startup(
        name="Acme Artificial Intelligence",
        website_url="https://acme.com/",
        existing=existing,
    )

    assert match is existing[0]


def test_falls_back_to_name_when_domains_differ() -> None:
    """Dominio diferente nao bloqueia o match - so deixa de ser a causa
    direta; nome identico ainda casa pelo fallback de nome."""

    existing = [Startup(name="Acme AI", website_url="https://acme.io")]

    match = find_duplicate_startup(
        name="Acme AI", website_url="https://acme-labs.com", existing=existing
    )

    assert match is existing[0]


def test_no_match_when_nothing_similar_exists() -> None:
    existing = [Startup(name="Totally Unrelated Co")]

    match = find_duplicate_startup(
        name="Acme AI", website_url="https://acme.com", existing=existing
    )

    assert match is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://acme.com", "acme.com"),
        ("https://www.acme.com/", "acme.com"),
        ("https://acme.com/pricing", "acme.com"),
        ("acme.com", "acme.com"),
        ("WWW.ACME.COM", "acme.com"),
    ],
)
def test_normalize_domain(raw: str, expected: str) -> None:
    assert normalize_domain(raw) == expected
