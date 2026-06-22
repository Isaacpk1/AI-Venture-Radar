"""Adaptador que le `chunks` (de `ingestion`) sem importar internals do modulo.

Usa SQL textual contra a tabela `chunks` para fazer busca lexical
(full-text search nativo do PostgreSQL), evitando qualquer dependencia
dos modelos ou repositorios do modulo ingestion. Mesmo padrao de
`ingestion/infrastructure/database/postgres_scraping_result_reader.py`
(que le `scraping_results` da mesma forma).

Config `'simple'` (sem stemming/stopwords por idioma) porque o conteudo
coletado mistura PT-BR e ingles. O indice GIN de expressao criado na
migration usa a mesma expressao (`to_tsvector('simple', text)`), por isso
a query abaixo precisa repetir a expressao identica para o planner usar o
indice.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.src.database.relational.session import AsyncSessionFactory
from apps.api.src.modules.rag.application.dto import LexicalSearchResult
from apps.api.src.modules.rag.application.ports import LexicalSearchRepository

_QUERY = text("""
    SELECT c.id, c.document_id,
           ts_rank(to_tsvector('simple', c.text), websearch_to_tsquery('simple', :query)) AS rank
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE to_tsvector('simple', c.text) @@ websearch_to_tsquery('simple', :query)
      AND (:source_type IS NULL OR d.source_type = :source_type)
    ORDER BY rank DESC
    LIMIT :limit
""")


class PostgresLexicalSearchRepository(LexicalSearchRepository):

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionFactory,
    ) -> None:
        self._session_factory = session_factory

    async def search(
        self,
        query: str,
        *,
        limit: int,
        source_type: str | None = None,
    ) -> list[LexicalSearchResult]:
        session = self._session_factory()
        try:
            result = await session.execute(
                _QUERY,
                {"query": query, "limit": limit, "source_type": source_type},
            )
            return [
                LexicalSearchResult(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    score=row.rank,
                )
                for row in result.fetchall()
            ]
        finally:
            await session.close()
