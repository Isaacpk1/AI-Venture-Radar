# Roadmap do Modulo RAG

O modulo `rag` responde perguntas usando evidencias recuperadas. Ele deve
buscar antes de gerar.

RAG significa Retrieval-Augmented Generation:

```txt
pergunta -> busca evidencias -> monta contexto -> LLM responde com fontes
```

---

## Objetivo do Modulo

```txt
responder perguntas sobre startups com base em evidencias citaveis
```

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| RAG V1 | Implementado | Busca semantica simples |
| RAG V2 | Implementado | Resposta com citacoes |
| RAG V3 | Implementado | Busca hibrida (vetorial + lexical, RRF) |
| RAG V4 | Implementado | Reranking (Cohere Rerank) |
| RAG V5 | Parcial (baseline Ragas medida) | Avaliacao de qualidade |

---

## RAG V1 - Busca Semantica Simples

Status:

```txt
implementado
```

Entregaveis:

- modulo `apps/api/src/modules/rag`;
- contrato publico `Retriever`;
- busca por similaridade no Qdrant;
- retorno de chunks com score e fonte;
- recuperacao do texto completo/metadados no PostgreSQL;
- rota `POST /rag/search`;
- testes com repositorio fake.

Criterio de pronto:

```txt
uma pergunta retorna chunks relevantes com referencia ao document/chunk original
```

Fora do escopo da V1:

```txt
resposta gerada por LLM
citacoes em texto final
busca hibrida
reranking
```

Documento da entrega: `docs/rag/rag_v1_busca_semantica.md`.

---

## RAG V2 - Resposta com Citacoes

Status:

```txt
implementado
```

Entregaveis:

- montagem de contexto;
- prompt de resposta fundamentada;
- saida estruturada com resposta e citacoes;
- validacao para impedir resposta sem fonte.
- rota `POST /rag/answer`;
- adapter Gemini via LangChain em `rag/infrastructure/llm`;
- fallback claro com 503 quando `GEMINI_API_KEY` nao esta configurada.

Documento da entrega: `docs/rag/rag_v2_resposta_com_citacoes.md`.

---

## RAG V3 - Busca Hibrida

Status:

```txt
implementado
```

**Nota sobre o nome:** "busca hibrida" aqui significa fusao
vetorial+lexical (Qdrant + PostgreSQL full-text search via RRF) — o que
o brief original do case pede (secao 5.3). Filtros estruturados
(startup/fonte/data/tipo de evidencia) sao uma melhoria diferente
("busca filtrada"), ainda nao implementada, e podem entrar numa V3.5
futura se houver necessidade.

Entregue:

- busca lexical via PostgreSQL full-text search nativo (`to_tsvector`/
  `websearch_to_tsquery`/`ts_rank`, indice GIN de expressao) — nao BM25
  via lib Python, para nao carregar chunks em memoria;
- fusao de ranking vetorial + lexical via Reciprocal Rank Fusion (RRF),
  `domain/policies.py::fuse_rankings()`;
- pool de candidatos maior que o limite final antes de fundir/rerankar;
- `LexicalSearchRepository` (contrato interno) +
  `PostgresLexicalSearchRepository` (SQL textual, sem importar internals
  de `ingestion`);
- migration `8d84cba84a02` (indice GIN).

Documento da entrega: `docs/rag/rag_v3_busca_hibrida.md`.

---

## RAG V4 - Reranking

Status:

```txt
implementado
```

Entregue:

- `CohereReranker` — usa **Cohere Rerank**, conforme o brief recomenda
  (secao 5.3); `COHERE_API_KEY` (ja em `Settings` desde o inicio do
  projeto) finalmente em uso;
- degradacao graciosa: sem API key, busca segue sem reranking (ordem da
  fusao RRF); falha em runtime do Cohere tambem degrada, nunca quebra a
  busca;
- reranking aplicado dentro de `SearchEvidence.search()` — beneficia
  `/rag/search` e `/rag/answer` ao mesmo tempo.

Documento da entrega: `docs/rag/rag_v4_reranking.md`.

---

## RAG V5 - Avaliacao

Status:

```txt
parcial — baseline de qualidade medida em 23/06/2026 (ver atualizacao
abaixo); dataset golden completo e regressao automatica continuam futuros
```

Entregaveis:

- dataset fixo de perguntas;
- avaliacao de citacoes;
- avaliacao de resposta sem alucinacao;
- regressao de prompt.

**Atualizacao 23/06/2026:** a Fase 2 de
`docs/roadmap_evolucao_tecnica_mvp.md` ja entregou a primeira parte desta
V5 — `tests/integration/test_ragas_quality_baseline.py` (opt-in via
`RUN_RAGAS_EVAL=1`), 12 perguntas sobre conteudo real do NVIDIA Knowledge
V2, com numero medido:

```txt
faithfulness        0.92
answer_relevancy    0.86
context_precision   0.90
context_recall      0.67
```

`context_recall` (0.67) e' o mais baixo dos 4 — e' o numero que decide a
Fase 3 daquele roadmap (BM25/`pg_search` so entra se uma mudanca de busca
melhorar esse numero de forma medida). Falta ainda: dataset crescer com
mais fontes do NVIDIA Knowledge V2 (hoje so 2/8 P0 validadas), e regressao
de prompt automatica (essa parte continua futura, depende de CI existir).

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| `context_recall` (0.67) e' o gargalo medido da V5; busca lexical usa `to_tsvector('simple')`, sem stemming ("treinar" != "treinamento") | avaliar `pg_search` (ParadeDB) como extensao Postgres para BM25 nativo — so depois de confirmar que o gargalo e' lexical, nao retrieval vetorial; decisao contra `rank-bm25` (Python) ja tomada e documentada em V3 acima | Fase 3 de `docs/roadmap_evolucao_tecnica_mvp.md` | Alto — troca de imagem Postgres + migration + reindexacao |
| Modelo do Cohere Rerank fixo em codigo (`rerank-v3.5`) | extrair para `Settings` (`COHERE_RERANK_MODEL`, default `rerank-v3.5`) — **concluido em 23/06/2026** | Fase 4 de `docs/roadmap_evolucao_tecnica_mvp.md` | Trivial |
| Filtro de busca so por `source_type`, nada por startup/data/categoria | estender `LexicalSearchRepository`/`VectorRepository` com filtros estruturados adicionais (sem lib nova, so mais parametros de query) | V3.5 mencionada acima ("busca filtrada") | Medio |

Nao reabrir `rank-bm25` (Python): exigiria carregar todos os chunks em
memoria a cada busca, contradizendo a regra de Postgres como fonte da
verdade — decisao ja tomada e ainda valida.
