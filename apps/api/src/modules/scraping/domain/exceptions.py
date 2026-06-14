"""Exceções conhecidas pelo domínio de scraping.

Essas exceções descrevem situações esperadas pelo negócio. Por exemplo:
solicitar um job inexistente ou tentar iniciar um job já concluído.

Elas não sabem como o erro será apresentado ao usuário. Posteriormente, a
camada ``presentation`` decidirá qual status HTTP corresponde a cada exceção.
"""


class ScrapingError(Exception):
    """Classe base para todos os erros conhecidos do módulo.

    Ter uma classe base permite capturar qualquer erro esperado do módulo sem
    esconder erros inesperados de programação.
    """


class InvalidJobTransitionError(ScrapingError):
    """O job tentou mudar para um estado que não é permitido.

    Exemplo: tentar mudar diretamente de ``pending`` para ``completed`` sem
    antes iniciar a execução.
    """


class ScrapingJobNotFoundError(ScrapingError):
    """O job de scraping solicitado não existe."""


class ScrapingResultNotFoundError(ScrapingError):
    """O resultado de scraping solicitado não existe."""


class ScrapingFailedError(ScrapingError):
    """Nenhuma estratégia conseguiu produzir conteúdo válido."""


class RecoverableScrapingError(ScrapingError):
    """Falha técnica que permite tentar outra estratégia de coleta.

    Exemplo: BeautifulSoup recebeu timeout, mas Playwright ainda pode conseguir
    abrir a mesma página.
    """


class ScrapingLimitExceededError(RecoverableScrapingError):
    """Uma estratégia individual excedeu um de seus limites operacionais."""


class ScrapingRequestError(RecoverableScrapingError):
    """A requisição HTTP falhou por timeout, conexão ou protocolo."""


class GlobalScrapingLimitExceededError(ScrapingError):
    """O job inteiro excedeu um limite e nenhuma estratégia deve continuar."""


class UnsafeUrlError(ScrapingError):
    """A URL foi recusada por ser inválida ou apresentar risco de SSRF."""
