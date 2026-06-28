"""Excecoes de dominio do modulo startup_discovery."""


class DiscoveryRunNotFoundError(Exception):
    """DiscoveryRun nao encontrado pelo id informado."""


class InvalidDiscoveryRunTransitionError(Exception):
    """Transicao de status invalida para um DiscoveryRun."""
