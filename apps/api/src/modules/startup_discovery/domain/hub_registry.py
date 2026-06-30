"""Registry dos hubs de descoberta de startups.

Cada `HubSource` aponta para a pagina de listagem de um hub. O extrator
correspondente (ver `infrastructure/hub_extractors/`) sabe como navegar
essa pagina e extrair URLs de startups individuais.

URLs e seletores podem precisar de ajuste se o hub mudar o layout — o
teste `pytest -k test_hub_scrapers` valida os extratores contra os sites
reais (requer rede).
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class HubSource:
    name: str
    listing_url: str
    extractor_type: str
    extraction_mode: Literal["url", "name"] = "url"


# Categorias do 100 Open Startups relevantes para o radar NVIDIA
OPEN_STARTUPS_CATEGORIES: list[str] = [
    "TOP 10 Artificial Intelligence 2025",
    "TOP 10 Big Data 2025",
    "TOP 10 Cybersecurity 2025",
    "TOP 10 FinTechs 2025",
    "TOP 10 HealthTechs 2025",
    "TOP 10 IndTechs 2025",
    "TOP 10 IoT 2025",
    "TOP 10 Productivity 2025",
]

HUB_SOURCES: list[HubSource] = [
    HubSource(
        name="InovAtiva Brasil",
        listing_url="https://inovativabrasil.com.br/empresas/",
        extractor_type="inovativa",
        extraction_mode="url",
    ),
    HubSource(
        name="Abstartups",
        listing_url="https://abstartups.com.br/startups-associadas/",
        extractor_type="abstartups",
        extraction_mode="url",
    ),
    HubSource(
        name="100 Open Startups",
        listing_url="https://www.openstartups.net/site/ranking/data/rankings/categories/2025.js",
        extractor_type="open_startups",
        extraction_mode="name",
    ),
]
