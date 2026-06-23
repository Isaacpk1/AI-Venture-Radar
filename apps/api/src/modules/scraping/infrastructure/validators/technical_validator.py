"""Validacao deterministica dos aspectos tecnicos de uma coleta."""

import re

from apps.api.src.modules.scraping.application.dto import (
    ScrapingOutput,
    ValidationComponentResult,
)


class TechnicalValidator:
    """Avalia se a pagina foi coletada de forma tecnicamente utilizavel."""

    # Sinais comuns de paginas que entregam apenas uma casca HTML e dependem
    # de JavaScript para preencher o conteudo principal.
    javascript_required_patterns = (
        re.compile(r"enable javascript", re.IGNORECASE),
        re.compile(r"javascript is required", re.IGNORECASE),
        re.compile(r"you need to enable javascript", re.IGNORECASE),
        re.compile(r"id=[\"'](?:root|app|__next)[\"'][^>]*>\s*</", re.IGNORECASE),
    )

    def validate(self, output: ScrapingOutput) -> ValidationComponentResult:
        """Calcula score tecnico, problemas bloqueadores e alertas."""

        score = 1.0
        problems: set[str] = set()
        warnings: set[str] = set()

        if not output.source_url:
            problems.add("missing_source_url")
            score -= 0.40

        if output.status_code >= 400:
            problems.add("blocked_status")
            score -= 0.60

        if "text/html" not in output.content_type.lower():
            problems.add("unsupported_content_type")
            score -= 0.40

        if not output.raw_html.strip():
            problems.add("empty_content")
            score -= 0.60

        if self._has_captcha_challenge(output):
            problems.add("captcha")
            score -= 0.60

        if self._requires_javascript(output):
            problems.add("javascript_required")
            score -= 0.30

        if output.final_url != output.source_url:
            warnings.add("redirected")

        return ValidationComponentResult(
            score=self._bounded(score),
            problems=problems,
            warnings=warnings,
        )

    def _has_captcha_challenge(self, output: ScrapingOutput) -> bool:
        """Detecta uma pagina de desafio real, nao so uma referencia a lib.

        Um match isolado de "captcha" no HTML nao prova um bloqueio: muitos
        sites legitimos carregam libs de captcha globalmente (ex: GitHub,
        para formularios de login/abuso) mesmo em paginas sem nenhum desafio
        sendo exibido para esta coleta. Paginas de desafio real (Cloudflare,
        reCAPTCHA, hCaptcha) sao curtas — quase todo o conteudo e o proprio
        widget — por isso exigimos o sinal textual combinado com pouco texto
        extraido, mesmo padrao usado em ``_requires_javascript``.
        """

        lowered_html = output.raw_html.lower()
        has_captcha_signal = "captcha" in lowered_html
        return has_captcha_signal and len(output.raw_text.strip()) < 500

    def _requires_javascript(self, output: ScrapingOutput) -> bool:
        """Detecta sinais fortes de uma pagina vazia antes da renderizacao."""

        # Playwright ja executou JavaScript; nesse caso, uma casca semelhante
        # nao deve solicitar outro fallback para a mesma tecnologia.
        if output.metadata.get("javascript_rendered") is True:
            return False

        html = output.raw_html.strip()
        text = output.raw_text.strip()
        has_javascript_signal = any(
            pattern.search(html) for pattern in self.javascript_required_patterns
        )

        return has_javascript_signal and len(text) < 300

    @staticmethod
    def _bounded(score: float) -> float:
        return round(max(0.0, min(score, 1.0)), 4)
