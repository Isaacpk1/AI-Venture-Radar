"""Registry dos hubs de descoberta de startups.

Cada `HubSource` aponta para a pagina de listagem de um hub. O extrator
correspondente (ver `infrastructure/hub_extractors/`) sabe como navegar
essa pagina e extrair URLs de startups individuais.

URLs e seletores podem precisar de ajuste se o hub mudar o layout — o
teste `pytest -k test_hub_scrapers` valida os extratores contra os sites
reais (requer rede).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HubSource:
    name: str
    listing_url: str
    extractor_type: str


HUB_SOURCES: list[HubSource] = [
    HubSource(
        name="InovAtiva Brasil",
        listing_url="https://inovativabrasil.com.br/empresas/",
        extractor_type="inovativa",
    ),
    HubSource(
        name="Abstartups",
        listing_url="https://abstartups.com.br/startups-associadas/",
        extractor_type="abstartups",
    ),
    HubSource(
        name="100 Open Startups",
        listing_url="https://www.openstartups.net/site/startups/ranking.html",
        extractor_type="open_startups",
    ),
]
