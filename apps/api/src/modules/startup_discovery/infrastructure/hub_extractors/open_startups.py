"""Extrator de links de startups do 100 Open Startups.

Estrategia: a pagina de ranking do 100 Open Startups
(https://www.openstartups.net/site/startups/ranking.html) exibe uma tabela
ou lista de startups ranqueadas. Cada entrada tem link para o perfil da
startup na plataforma, que por sua vez tem o site oficial.

O site do 100 Open Startups tende a ter markup bem estruturado com links
`<a>` nas linhas da tabela de ranking.

Ajuste `_ROW_SELECTOR` e `_WEBSITE_SELECTOR` se o layout mudar.
"""

from apps.api.src.modules.startup_discovery.infrastructure.hub_extractors.base import (
    BaseHubLinkExtractor,
)

_HUB_DOMAIN = "openstartups.net"
_ROW_SELECTOR = "table tr a, .ranking-row a, .startup-row a, .ranking a[href*='startup']"
_WEBSITE_SELECTOR = "a.website, a[rel='nofollow external'], .startup-website a, a[target='_blank']"


class OpenStartupsExtractor(BaseHubLinkExtractor):

    async def extract(self, listing_url: str, *, limit: int) -> list[str]:
        soup = await self._fetch(listing_url)

        # Tentativa 1: links externos diretos na listagem (alguns rankings
        # tem o site da startup direto na linha da tabela)
        external: list[str] = []
        for tag in soup.find_all("a", href=True):
            href: str = tag["href"]
            if self._is_external(href, _HUB_DOMAIN) and "." in href.split("/")[-1]:
                external.append(href)
            if len(external) >= limit:
                break

        if len(external) >= 3:
            return self._normalize(external)[:limit]

        # Tentativa 2: perfis internos -> extrair website de cada perfil
        profile_links: list[str] = []
        for tag in soup.select(_ROW_SELECTOR):
            href = tag.get("href", "")
            if href:
                full = href if href.startswith("http") else f"https://{_HUB_DOMAIN}{href}"
                profile_links.append(full)

        websites: list[str] = []
        for profile_url in profile_links[:limit]:
            try:
                detail = await self._fetch(profile_url)
                for tag in detail.select(_WEBSITE_SELECTOR):
                    href = tag.get("href", "")
                    if self._is_external(href, _HUB_DOMAIN) and "linkedin" not in href:
                        websites.append(href)
                        break
            except Exception:
                continue

        return self._normalize(websites + external)[:limit]
