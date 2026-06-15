"""Orquestração principal da coleta e validação de conteúdo."""

import asyncio
from hashlib import sha256
from uuid import UUID

from apps.api.src.modules.scraping.domain.entities import ScrapingAttempt, ScrapingResult
from apps.api.src.modules.scraping.domain.enums import (
    AttemptStatus,
    SemanticReviewDecision,
    ValidationDecision,
)
from apps.api.src.modules.scraping.domain.exceptions import (
    GlobalScrapingLimitExceededError,
    RecoverableScrapingError,
    ScrapingFailedError,
)
from apps.api.src.modules.scraping.domain.policies import (
    LLMReviewPolicy,
    ValidationDecisionPolicy,
)
from apps.api.src.modules.scraping.domain.repositories import ScrapingAttemptRepository

from .dto import ScrapingInput, SemanticValidationInput
from .ports import DeterministicValidator, SemanticValidator
from .quality_scoring_service import QualityScoringService
from .scraping_limits import PipelineLimits
from .semantic_confidence_service import SemanticConfidenceService
from .strategy_selector import ScrapingStrategySelector


class ScrapingPipeline:
    """Coordena componentes especializados sem implementar o trabalho deles.

    A pipeline não conhece BeautifulSoup e não calcula scores diretamente. Ela
    apenas organiza a ordem das operações e entrega cada tarefa ao componente
    responsável.
    """

    def __init__(
        self,
        strategy_selector: ScrapingStrategySelector,
        validator: DeterministicValidator,
        scoring_service: QualityScoringService,
        decision_policy: ValidationDecisionPolicy,
        attempt_repository: ScrapingAttemptRepository,
        limits: PipelineLimits | None = None,
        llm_review_policy: LLMReviewPolicy | None = None,
        semantic_validator: SemanticValidator | None = None,
        semantic_confidence_service: SemanticConfidenceService | None = None,
    ) -> None:
        """Recebe todas as dependências necessárias para executar o fluxo."""

        self.strategy_selector = strategy_selector
        self.validator = validator
        self.scoring_service = scoring_service
        self.decision_policy = decision_policy
        self.attempt_repository = attempt_repository
        self.limits = limits or PipelineLimits()
        self.llm_review_policy = llm_review_policy or LLMReviewPolicy()
        self.semantic_validator = semantic_validator
        self.semantic_confidence_service = (
            semantic_confidence_service or SemanticConfidenceService()
        )

    async def execute(
        self,
        job_id: UUID,
        url: str,
    ) -> ScrapingResult:
        """Executa estratégias até produzir um resultado aprovado.

        Conteúdos rejeitados não se transformam em ``ScrapingResult``. Quando
        nenhuma estratégia consegue produzir conteúdo aceito, a pipeline
        informa a falha ao caso de uso por meio de ``ScrapingFailedError``.
        """

        try:
            async with asyncio.timeout(self.limits.total_timeout_seconds):
                return await self._execute_with_limits(job_id, url)
        except TimeoutError as error:
            raise GlobalScrapingLimitExceededError(
                "O job excedeu o timeout total de "
                f"{self.limits.total_timeout_seconds}s."
            ) from error

    async def _execute_with_limits(
        self,
        job_id: UUID,
        url: str,
    ) -> ScrapingResult:
        """Executa a pipeline já protegida pelo timeout global."""

        selected_strategies = self.strategy_selector.select(url)

        # Mesmo que a factory configure estratégias demais, o job respeita o
        # teto global e nunca tenta além da quantidade permitida.
        strategies = selected_strategies[: self.limits.max_strategies]
        strategies_were_limited = len(selected_strategies) > len(strategies)

        # ``enumerate`` fornece a posição atual para descobrirmos se existe
        # outra estratégia disponível depois da tentativa atual.
        for index, scraper in enumerate(strategies):
            has_next_strategy = index < len(strategies) - 1

            # Cada tecnologia tentada gera um registro de auditoria separado.
            attempt = ScrapingAttempt(
                job_id=job_id,
                method=scraper.method,
            )
            await self.attempt_repository.save(attempt)

            try:
                output = await scraper.scrape(ScrapingInput(url=url))
                validation_without_score = await self.validator.validate(output)
                validation = self.scoring_service.calculate(
                    validation_without_score
                )

                decision = self.decision_policy.decide(
                    validation.to_summary(),
                    has_next_strategy=has_next_strategy,
                )
                attempt_warnings = set(validation.warnings)
                semantic_metadata: dict[str, str | float | bool] = {}

                # A revisao semantica interpreta somente conteudo ambiguo que
                # ja passou pelos requisitos tecnicos e textuais minimos.
                if (
                    decision is ValidationDecision.REJECT
                    and self.semantic_validator is not None
                    and self.llm_review_policy.requires_review(
                        validation.to_summary()
                    )
                ):
                    assessment = await self.semantic_validator.validate(
                        SemanticValidationInput(
                            url=output.final_url,
                            title=output.title,
                            raw_text=output.raw_text,
                            deterministic=validation,
                        )
                    )
                    semantic = self.semantic_confidence_service.calculate(assessment)
                    attempt_warnings.add("semantic_reviewed")
                    attempt_warnings.add(
                        f"semantic_decision_{assessment.decision.value}"
                    )
                    semantic_metadata = {
                        "semantic_reviewed": True,
                        "semantic_decision": assessment.decision.value,
                        "semantic_confidence": semantic.semantic_confidence,
                        "semantic_reason": assessment.reason,
                        "semantic_contradiction_detected": (
                            assessment.contradiction_detected
                        ),
                    }

                    if (
                        assessment.decision is SemanticReviewDecision.ACCEPTED
                        and semantic.semantic_confidence >= 0.80
                    ):
                        decision = ValidationDecision.ACCEPT

                attempt.finish_validation(
                    decision=decision,
                    technical_score=validation.technical_score,
                    text_score=validation.text_score,
                    evidence_score=validation.evidence_score,
                    quality_score=validation.quality_score,
                    problems=list(validation.problems),
                    warnings=list(attempt_warnings),
                )
                await self.attempt_repository.save(attempt)

                # FALLBACK significa que esta execução terminou normalmente,
                # mas outra tecnologia deve tentar coletar a mesma URL.
                if decision is ValidationDecision.FALLBACK:
                    continue

                if decision is ValidationDecision.REJECT:
                    raise ScrapingFailedError(
                        "O conteúdo coletado foi rejeitado pela validação."
                    )

                # Apenas uma decisão ACCEPT produz a saída oficial do módulo.
                return ScrapingResult(
                    job_id=job_id,
                    url=output.source_url,
                    final_url=output.final_url,
                    title=output.title,
                    raw_html=output.raw_html,
                    raw_text=output.raw_text,
                    method=output.method,
                    status_code=output.status_code,
                    technical_score=validation.technical_score,
                    text_score=validation.text_score,
                    evidence_score=validation.evidence_score,
                    quality_score=validation.quality_score,
                    content_hash=sha256(
                        output.raw_text.encode("utf-8")
                    ).hexdigest(),
                    metadata={**output.metadata, **semantic_metadata},
                )
            except Exception as error:
                if attempt.status is AttemptStatus.RUNNING:
                    attempt.fail(str(error))
                    await self.attempt_repository.save(attempt)

                # Rejeição é uma decisão de negócio, não uma falha técnica que
                # outra tecnologia de coleta conseguiria corrigir.
                if isinstance(error, ScrapingFailedError):
                    raise

                # Somente falhas técnicas conhecidas como recuperáveis podem
                # trocar de tecnologia. Bugs e erros fatais são propagados.
                if isinstance(error, RecoverableScrapingError) and has_next_strategy:
                    continue

                if isinstance(error, RecoverableScrapingError) and strategies_were_limited:
                    raise GlobalScrapingLimitExceededError(
                        "O job atingiu o máximo de "
                        f"{self.limits.max_strategies} estratégias."
                    ) from error

                if not isinstance(error, RecoverableScrapingError):
                    raise

                raise ScrapingFailedError(
                    f"A estratégia {scraper.method} falhou: {error}"
                ) from error

        if strategies_were_limited:
            raise GlobalScrapingLimitExceededError(
                "O job atingiu o máximo de "
                f"{self.limits.max_strategies} estratégias."
            )

        raise ScrapingFailedError("Nenhuma estratégia produziu conteúdo aprovado.")
