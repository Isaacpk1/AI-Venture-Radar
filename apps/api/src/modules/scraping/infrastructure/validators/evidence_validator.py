"""Validacao deterministica de sinais evidenciais do conteudo."""

import re

from apps.api.src.modules.scraping.application.dto import (
    ScrapingOutput,
    ValidationComponentResult,
)


class EvidenceValidator:
    """Mede sinais objetivos de IA, produto e descricao de capacidade."""

    ai_terms = (
        "ai",
        "artificial intelligence",
        "inteligencia artificial",
        "inteligência artificial",
        "machine learning",
        "deep learning",
        "generative ai",
        "ia generativa",
        "computer vision",
        "visao computacional",
        "visão computacional",
        "language model",
        "modelo de linguagem",
    )

    product_terms = (
        "platform",
        "plataforma",
        "product",
        "produto",
        "solution",
        "solucao",
        "solução",
        "service",
        "servico",
        "serviço",
        "software",
        "api",
    )

    capability_terms = (
        "helps",
        "ajuda",
        "automates",
        "automatiza",
        "analyzes",
        "analisa",
        "detects",
        "detecta",
        "predicts",
        "preve",
        "prevê",
        "optimizes",
        "otimiza",
        "enables",
        "permite",
    )

    def validate(self, output: ScrapingOutput) -> ValidationComponentResult:
        """Calcula evidencia sem realizar interpretacao semantica com IA."""

        text = output.raw_text.lower()
        title = (output.title or "").lower()
        searchable_content = f"{title}\n{text}"
        warnings: set[str] = set()

        matched_ai_terms = self._matched_terms(searchable_content, self.ai_terms)
        matched_product_terms = self._matched_terms(
            searchable_content,
            self.product_terms,
        )
        matched_capability_terms = self._matched_terms(
            searchable_content,
            self.capability_terms,
        )

        if not matched_ai_terms:
            warnings.add("no_ai_evidence_signal")
        if not matched_product_terms:
            warnings.add("no_product_signal")
        if not matched_capability_terms:
            warnings.add("no_capability_description")
        if not output.title:
            warnings.add("missing_title")

        # IA e o sinal principal. Produto e capacidade ajudam a diferenciar
        # uma descricao real de uma pagina que apenas menciona termos de IA.
        score = 0.10
        score += min(len(matched_ai_terms) * 0.15, 0.45)
        score += min(len(matched_product_terms) * 0.08, 0.20)
        score += min(len(matched_capability_terms) * 0.08, 0.20)

        # A combinacao das tres categorias e mais informativa que palavras
        # isoladas: descreve uma tecnologia, apresentada como produto, com uma
        # capacidade concreta.
        if matched_ai_terms and matched_product_terms and matched_capability_terms:
            score += 0.20

        if output.title:
            score += 0.05

        return ValidationComponentResult(
            score=self._bounded(score),
            warnings=warnings,
        )

    def _matched_terms(self, text: str, terms: tuple[str, ...]) -> set[str]:
        """Encontra termos completos para reduzir coincidencias acidentais."""

        return {
            term
            for term in terms
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text)
        }

    @staticmethod
    def _bounded(score: float) -> float:
        return round(max(0.0, min(score, 1.0)), 4)
