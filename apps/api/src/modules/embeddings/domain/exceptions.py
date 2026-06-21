"""Excecoes do dominio do modulo embeddings."""


class EmbeddingsError(Exception):
    """Base para todas as excecoes do modulo embeddings."""


class EmptyChunkTextError(EmbeddingsError):
    """Nao e possivel gerar embedding de um texto vazio."""


class InvalidEmbeddingDimensionError(EmbeddingsError):
    """O vetor gerado nao tem a dimensao esperada."""


class EmbeddingServiceUnavailableError(EmbeddingsError):
    """O provider de embeddings nao esta configurado (ex: chave de API ausente)."""


class EmbeddingGenerationError(EmbeddingsError):
    """O provider de embeddings nao conseguiu gerar o vetor."""
