"""Regras deterministicas de dominio do modulo startups."""

import re
from urllib.parse import urlparse

from rapidfuzz import fuzz

from apps.api.src.modules.startups.domain.entities import Startup

NAME_SIMILARITY_THRESHOLD = 92.0
"""Calibrado com pares reais (ver test_startup_deduplication_policy.py).

92 e' o menor valor que ainda captura toda variacao de nome
inequivocamente da mesma empresa observada na calibracao (maiusculas,
espacamento, sufixo legal — "OpenAI"/"Open AI" e' o caso mais baixo,
92.31) sem aceitar nenhum par de empresas diferentes testado (o mais
alto, "Stone"/"StoneAge" e "Acme AI"/"Acme Robotics", fica em 90 —
nome curto + sufixo comum e' uma colisao genuinamente ambigua sem o
dominio como segundo sinal, e o erro mais caro aqui e' fundir duas
empresas diferentes, nao deixar de detectar uma duplicata).
"""

_LEGAL_SUFFIXES = re.compile(
    r"\b(inc|incorporated|ltda|ltd|llc|sa|corp|corporation|co|tecnologia|tech|company)\b",
    re.IGNORECASE,
)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _normalize_name(name: str) -> str:
    normalized = _LEGAL_SUFFIXES.sub("", name.lower())
    return _NON_ALNUM.sub(" ", normalized).strip()


def normalize_domain(website_url: str) -> str:
    """Extrai o dominio (sem `www.`/protocolo/path) para comparar URLs."""

    candidate = website_url if "//" in website_url else f"//{website_url}"
    host = urlparse(candidate).netloc.lower()
    return host.removeprefix("www.")


def find_duplicate_startup(
    *,
    name: str,
    website_url: str | None,
    existing: list[Startup],
) -> Startup | None:
    """Acha, entre `existing`, a startup que provavelmente e' a mesma empresa.

    Dominio (apos normalizar `www.`/protocolo/path) e' o sinal mais
    confiavel: bate exato -> duplicata certa, sem fuzzy. Nome via
    rapidfuzz (`WRatio`) e' so um fallback para quando o dominio nao bate
    ou esta ausente — mais fraco, por isso o limiar e' alto (ver
    `NAME_SIMILARITY_THRESHOLD`).
    """

    candidate_domain = normalize_domain(website_url) if website_url else None
    candidate_name = _normalize_name(name)

    best_match: Startup | None = None
    best_score = 0.0
    for startup in existing:
        if candidate_domain and startup.website_url:
            if normalize_domain(startup.website_url) == candidate_domain:
                return startup

        score = fuzz.WRatio(candidate_name, _normalize_name(startup.name))
        if score > best_score:
            best_score = score
            best_match = startup

    if best_match is not None and best_score >= NAME_SIMILARITY_THRESHOLD:
        return best_match
    return None
