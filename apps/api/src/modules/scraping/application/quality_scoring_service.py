"""Serviço responsável por calcular a nota final de qualidade."""

from dataclasses import replace

from .dto import DeterministicValidationResult


class QualityScoringService:
    """Calcula o ``quality_score`` usando os pesos definidos no projeto.

    Este serviço fica na camada de aplicação porque coordena scores produzidos
    por diferentes validadores. Ele não coleta páginas e não decide se o
    conteúdo será aceito; essa decisão continua pertencendo às políticas.
    """

    technical_weight = 0.30
    text_weight = 0.30
    evidence_weight = 0.40

    def calculate(
        self,
        validation: DeterministicValidationResult,
    ) -> DeterministicValidationResult:
        """Retorna uma nova validação contendo o score final calculado."""

        quality_score = (
            validation.technical_score * self.technical_weight
            + validation.text_score * self.text_weight
            + validation.evidence_score * self.evidence_weight
        )

        # O DTO é imutável. ``replace`` cria uma cópia, alterando somente o
        # quality_score e preservando scores, problemas e warnings originais.
        return replace(
            validation,
            quality_score=round(quality_score, 4),
        )
