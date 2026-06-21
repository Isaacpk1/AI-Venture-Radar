"""Servico de divisao de texto em chunks para embedding."""


class TextChunker:
    """Divide texto limpo em fragmentos de tamanho controlado com sobreposicao.

    Estrategia de V1: baseada em caracteres, com preferencia por quebras em
    paragrafo > sentenca > palavra. Chunks pequenos demais (< 50 chars apos
    strip) sao descartados para evitar ruido no embedding.
    """

    _MIN_CHUNK_CHARS = 50

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        if len(text) <= self._chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = min(start + self._chunk_size, len(text))

            if end >= len(text):
                candidate = text[start:].strip()
                if len(candidate) >= self._MIN_CHUNK_CHARS:
                    chunks.append(candidate)
                break

            break_pos = self._find_break(text, start, end)

            candidate = text[start:break_pos].strip()
            if len(candidate) >= self._MIN_CHUNK_CHARS:
                chunks.append(candidate)

            # Proximo chunk comeca com sobreposicao em relacao ao break_pos
            start = max(start + 1, break_pos - self._chunk_overlap)

        return chunks

    def _find_break(self, text: str, start: int, end: int) -> int:
        """Encontra a melhor posicao de quebra antes de ``end``."""

        # Paragrafo (linha dupla)
        pos = text.rfind("\n\n", start, end)
        if pos > start:
            return pos + 2

        # Sentenca
        pos = text.rfind(". ", start, end)
        if pos > start:
            return pos + 2

        # Palavra
        pos = text.rfind(" ", start, end)
        if pos > start:
            return pos + 1

        return end
