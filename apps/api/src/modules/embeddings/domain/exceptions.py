"""Excecoes do dominio do modulo embeddings."""


class EmbeddingsError(Exception):
    """Base para todas as excecoes do modulo embeddings."""


class EmptyChunkTextError(EmbeddingsError):
    """Nao e possivel gerar embedding de um texto vazio."""


class InvalidEmbeddingDimensionError(EmbeddingsError):
    """O vetor gerado nao tem a dimensao esperada."""
