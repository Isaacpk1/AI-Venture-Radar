"""Excecoes do modulo startups."""


class StartupError(Exception):
    """Erro base do modulo startups."""


class StartupNotFoundError(StartupError):
    """Startup nao encontrada."""


class StartupEvidenceNotFoundError(StartupError):
    """Evidencia de startup nao encontrada."""


class InvalidStartupDataError(StartupError):
    """Dados invalidos para criar ou atualizar startup."""
