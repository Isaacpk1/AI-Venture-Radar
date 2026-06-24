"""Adaptador que le `chunks` (de `ingestion`) sem importar internals do modulo.

Usa SQL textual contra a tabela `chunks` para fazer busca lexical via BM25
nativo (extensao `pg_search`/ParadeDB), evitando qualquer dependencia dos
modelos ou repositorios do modulo ingestion. Mesmo padrao de
`ingestion/infrastructure/database/postgres_scraping_result_reader.py`
(que le `scraping_results` da mesma forma).

Trocado de `to_tsvector('simple')`/`ts_rank` pra BM25 em 23/06/2026 (Fase 3
de docs/roadmap_evolucao_tecnica_mvp.md — baseline Ragas mediu
context_recall 0.67, considerado fraco). Indice `ix_chunks_bm25`
(`USING bm25 (id, text)`) criado na migration `b3f6e91c7d45` — exige a
extensao `pg_search` e a imagem `paradedb/paradedb:latest-pg16` em
`infra/docker-compose.yml` (pg_search nao tem binario pra Alpine/musl).
Operador `@@@` e `paradedb.score()` confirmados testando direto contra um
container real antes de escrever esta versao (ver
docs/rag/roadmap_rag.md).
"""

from sqlalchemy import String, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.src.database.relational.session import AsyncSessionFactory
from apps.api.src.modules.rag.application.dto import LexicalSearchResult
from apps.api.src.modules.rag.application.ports import LexicalSearchRepository

_QUERY = text("""
    SELECT c.id, c.document_id, paradedb.score(c.id) AS rank
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE c.text @@@ :query
      AND (:source_type IS NULL OR d.source_type = :source_type)
    ORDER BY rank DESC
    LIMIT :limit
""").bindparams(bindparam("source_type", type_=String()))


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
