"""Implementacao base compartilhada pelos extratores de links de hubs."""

import httpx
from bs4 import BeautifulSoup

from apps.api.src.modules.startup_discovery.application.ports import (
    HubLinkExtractor,
)

FETCH_TIMEOUT = 30
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NvidiaStartupRadar/1.0; +https://radar.example.com)"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


class BaseHubLinkExtractor(HubLinkExtractor):
    """Classe base com utilitarios de fetch/normalizacao para extratores concretos."""

    async def _fetch(self, url: str) -> BeautifulSoup:
        async with httpx.AsyncClient(
            timeout=FETCH_TIMEOUT,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _is_external(self, href: str, hub_domain: str) -> bool:
        return (
            href.startswith("http")
            and hub_domain not in href
            and not href.startswith("#")
        )

    def _normalize(self, urls: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for url in urls:
            url = url.rstrip("/")
            if url not in seen:
                seen.add(url)
                result.append(url)
        return result
