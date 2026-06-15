"""Testes da composicao concreta do modulo de scraping."""

from apps.api.src.modules.scraping.domain.enums import ScrapingMethod
from apps.api.src.modules.scraping.factories.scraping_factory import ScrapingFactory
from apps.api.src.modules.scraping.infrastructure.repositories.in_memory_attempt_repository import (
    InMemoryScrapingAttemptRepository,
)


def test_factory_configures_playwright_after_beautifulsoup() -> None:
    """A estrategia barata deve executar antes do fallback com navegador."""

    pipeline = ScrapingFactory.create_pipeline(InMemoryScrapingAttemptRepository())
    strategies = pipeline.strategy_selector.select("https://example.com")

    assert [strategy.method for strategy in strategies] == [
        ScrapingMethod.BEAUTIFULSOUP,
        ScrapingMethod.PLAYWRIGHT,
    ]
