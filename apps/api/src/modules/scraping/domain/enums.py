"""Enums que representam estados e decisões conhecidos pelo domínio.

Este arquivo pertence à camada ``domain`` porque esses valores fazem parte das
regras do negócio. Eles não dependem de FastAPI, banco de dados ou biblioteca
de scraping.
"""

from enum import StrEnum


class JobStatus(StrEnum):
    """Estado atual do processo completo de scraping."""

    # O job foi criado, mas ainda não começou a ser executado.
    PENDING = "pending"

    # O worker iniciou a execução do job.
    RUNNING = "running"

    # Um conteúdo válido foi coletado e salvo como resultado.
    COMPLETED = "completed"

    # O job terminou sem conseguir produzir um resultado válido.
    FAILED = "failed"

    # O job foi interrompido intencionalmente.
    CANCELLED = "cancelled"


class AttemptStatus(StrEnum):
    """Estado de uma tentativa feita com uma estratégia específica."""

    # A estratégia, por exemplo BeautifulSoup, está sendo executada.
    RUNNING = "running"

    # A tentativa produziu conteúdo aprovado.
    ACCEPTED = "accepted"

    # A tentativa não foi boa, mas vale tentar outra estratégia.
    FALLBACK = "fallback"

    # O conteúdo foi coletado, porém não deve ser aceito.
    REJECTED = "rejected"

    # A tentativa sofreu uma falha técnica inesperada.
    FAILED = "failed"


class ScrapingMethod(StrEnum):
    """Tecnologias de coleta que o módulo reconhece."""

    # Primeira estratégia para páginas com HTML estático.
    BEAUTIFULSOUP = "beautifulsoup"

    # Estratégia futura para páginas que dependem de JavaScript.
    PLAYWRIGHT = "playwright"


class ValidationDecision(StrEnum):
    """Decisões que a validação pode tomar sobre uma tentativa."""

    # O resultado pode seguir para a próxima etapa do sistema.
    ACCEPT = "accept"

    # Outra tecnologia deve tentar coletar a mesma URL.
    FALLBACK = "fallback"

    # O conteúdo não deve ser utilizado.
    REJECT = "reject"
