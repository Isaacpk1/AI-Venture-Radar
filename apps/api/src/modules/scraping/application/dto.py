"""Objetos usados para transportar dados dentro da camada de aplicação.

DTO significa Data Transfer Object. Diferente das entidades do domínio, DTOs
não protegem regras de negócio ou possuem ciclo de vida. Eles apenas definem um
formato estável para a comunicação entre as partes do módulo.
"""

from dataclasses import dataclass, field

from apps.api.src.modules.scraping.domain.enums import ScrapingMethod
from apps.api.src.modules.scraping.domain.policies import ValidationSummary


@dataclass(frozen=True)
class ScrapingInput:
    """Dados que a aplicação entrega para qualquer estratégia de scraping."""

    # Começaremos recebendo somente uma URL. No futuro, este DTO pode ganhar
    # timeout, cabeçalhos permitidos ou contexto da startup.
    url: str


@dataclass(frozen=True)
class ScrapingOutput:
    """Resultado técnico padronizado produzido por qualquer scraper.

    BeautifulSoup, Playwright e Firecrawl deverão devolver o mesmo formato.
    Dessa forma, a pipeline não precisa conhecer detalhes dessas tecnologias.
    """

    # URL originalmente solicitada.
    source_url: str

    # URL final, importante para detectar e auditar redirecionamentos.
    final_url: str

    title: str | None
    raw_html: str
    raw_text: str

    status_code: int
    content_type: str
    method: ScrapingMethod

    # Metadados adicionais não essenciais ao contrato principal.
    metadata: dict[str, str | int | float | bool | None] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class DeterministicValidationResult:
    """Medições objetivas produzidas pelos validadores.

    Os validadores técnicos e textuais preenchem este DTO. O método
    ``to_summary`` remove o detalhe de transporte e entrega ao domínio apenas
    os valores necessários para suas políticas.
    """

    technical_score: float
    text_score: float
    evidence_score: float
    quality_score: float = 0.0
    problems: set[str] = field(default_factory=set)
    warnings: set[str] = field(default_factory=set)

    def to_summary(self) -> ValidationSummary:
        """Converte o resultado da aplicação para o formato do domínio."""

        return ValidationSummary(
            technical_score=self.technical_score,
            text_score=self.text_score,
            evidence_score=self.evidence_score,
            quality_score=self.quality_score,
            problems=self.problems,
            warnings=self.warnings,
        )
