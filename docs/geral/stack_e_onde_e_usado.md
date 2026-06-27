# Stack e Onde Cada Tecnologia é Usada

Este documento lista cada tecnologia do projeto e onde ela entra na arquitetura.
"Em uso" significa import real no código; "Candidata" significa registrada em
algum `docs/<modulo>/roadmap.md` mas ainda não implementada.

Regra de leitura (do PRE-DECISION CHECKLIST do `CLAUDE.md`):

```txt
domain/         nunca importa tecnologia de infraestrutura
application/    nunca importa framework externo (só tipos/portas próprias)
infrastructure/ é onde toda tecnologia concreta realmente vive
factories/      é o único lugar que escolhe a implementação concreta de cada porta
graphs/         (só em agents) usa LangGraph; importa application/+domain/, nunca infra de outro módulo
```

---

## 1. Transversal / infraestrutura

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| Python 3.13 | runtime da API e workers | Em uso | Linguagem base |
| FastAPI | `presentation/` de todos os módulos | Em uso | Framework HTTP; nunca em domain/application |
| Pydantic / Pydantic Settings | schemas, settings, saída de LLM | Em uso | Validação estrutural; `config/settings.py` centraliza env vars |
| SQLAlchemy (async) | `infrastructure/database/` | Em uso | ORM confinado à infra para manter domain puro |
| PostgreSQL | toda tabela do projeto | Em uso | Fonte da verdade: status, auditoria, relacionamentos |
| Alembic | migrations na raiz | Em uso | Versionamento de schema, uma migration por entrega |
| Qdrant | `infrastructure/qdrant/` (embeddings) | Em uso | Busca por similaridade; todo vetor referencia ID do Postgres |
| Redis | broker do Dramatiq | Em uso | Fila assíncrona compartilhada por todos os workers |
| Dramatiq | toda fila assíncrona (5 workers) | Em uso | Mensagens carregam só job_id/run_id; retry/backoff nativo |
| Langfuse (self-hosted v3) | `shared/observability/` | Em uso (opcional) | Tracing de chamadas LLM (custo/latência) sem reescrever prompts |
| Docker Compose | `infra/docker-compose.yml` | Em uso | Postgres/Redis/Qdrant/Langfuse locais; sem Dockerfile de API ainda |
| Pytest | `apps/api/.../tests/` | Em uso | ~617 testes coletados no backend |

---

## 2. Scraping

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| BeautifulSoup | `infrastructure/scrapers/` | Em uso | Páginas estáticas (1ª tentativa) |
| Playwright | `infrastructure/scrapers/` | Em uso | Páginas com JavaScript pesado |
| Trafilatura | `infrastructure/scrapers/` | Em uso | Isola conteúdo principal em páginas densas |
| httpx (Gemini via HTTP) | `infrastructure/semantic_validators/` | Em uso | Validação semântica leve sem trazer LangChain |
| Firecrawl | — | Candidata | Fallback pago para páginas que esgotam BS4/Playwright/Trafilatura |

---

## 3. Ingestion

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| (sem lib externa) | `application/text_chunker.py`, `text_cleaner.py` | Em uso | Split manual por parágrafo/sentença/palavra |
| `langchain_text_splitters` | mesmo contrato | Candidata | Chunking estrutural sem lib nova (LangChain já é dependência) |

---

## 4. Embeddings

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| `langchain_google_genai` (`GoogleGenerativeAIEmbeddings`) | `infrastructure/gemini/` | Em uso | Implementa `EmbeddingService`; modelo `models/gemini-embedding-001` |
| `qdrant-client` (`AsyncQdrantClient`) | `infrastructure/qdrant/` | Em uso | Upsert/busca; cria coleção idempotente na 1ª chamada |
| hash SHA-256 (stdlib) | `infrastructure/` | Em uso | Cache por content_hash para não rechamar Gemini em texto idêntico |

---

## 5. Agents

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| LangGraph | `graphs/` (8 grafos) | Em uso | Orquestra os nodes de cada agente |
| LangChain (`ChatGoogleGenerativeAI`) | `infrastructure/llm/` | Em uso | Integra o Gemini aos nodes |
| Pydantic | saída de todo LLM client | Em uso | Resposta do LLM validada estruturalmente |
| PostgreSQL (checkpoints) | `infrastructure/checkpoints/` | Em uso | Estado do LangGraph por thread_id (human-in-the-loop) |
| Tavily | `infrastructure/search_adapters/` | Em uso (opcional) | Search Planner Agent → URLs externas quando `TAVILY_API_KEY` existe |

---

## 6. RAG

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| `pg_search` (ParadeDB, BM25 nativo) | imagem `paradedb/paradedb:latest-pg16` + repo lexical | Em uso | Substituiu `to_tsvector`/`ts_rank`; melhora context_recall sem carregar chunks na memória |
| Cohere (`AsyncClient.rerank`) | `infrastructure/reranking/` | Em uso | Reordena candidatos; degrada graciosamente sem `COHERE_API_KEY` |
| Ragas | `tests/integration/test_ragas_quality_baseline.py` | Em uso (opt-in `RUN_RAGAS_EVAL=1`) | Mede faithfulness/relevancy/precision/recall |

---

## 7. NVIDIA Knowledge

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| catálogo estático em código | `infrastructure/static_catalog/` | Em uso | 18 tecnologias/programas; dado não muda o suficiente para virar tabela |
| health-check HTTP HEAD | `infrastructure/` | Candidata | Detectar fontes do registry fora do ar antes de reingerir |

---

## 8. Startups

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| (sem lib externa) | `application/use_cases/`, `domain/` | Em uso | Modelo relacional + casos de uso simples |
| `rapidfuzz` | `domain/policies.py` (dedup) | Em uso | Dedup por nome/website antes de criar Startup; limiar 92 calibrado |
| JSONB (`ai_profile`) | `infrastructure/database/` | Em uso | StartupAIProfile estruturado (workload, deploy, GPU, etc.) |

---

## 9. Recommendations

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| `re` (regex, stdlib) | `domain/policies.py::_contains_term()` | Em uso | Word-boundary matching (fix do bug de substring "agent" em "agentes") |
| `rag.public.question_answerer` (reuso) | `infrastructure/rag_adapters/` | Em uso | Fundamenta justificativa em conteúdo NVIDIA real (citações) |
| `rag.public.retriever` (reuso) | `infrastructure/rag_adapters/` | Em uso | Prefiltro semântico de candidatos antes do keyword matching |

---

## 10. Briefing

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| string/Markdown puro | `domain/policies.py::build_briefing_markdown()` | Em uso | Saída determinística, sem template engine |
| Playwright + Jinja2 + `markdown` | `infrastructure/rendering/` | Em uso | Export PDF a partir do mesmo Markdown; trocou weasyprint para evitar deps nativas |

---

## 11. Orchestration

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| Dramatiq + Redis | `infrastructure/queue/` | Em uso | A fila `url_ingestion` é o próprio loop de polling |
| URLs same-domain + fila | `application/use_cases/advance_url_ingestion_job.py` | Em uso | 1ª fatia da chain de enriquecimento |
| Tavily + Search Planner (reuso) | adapters de enriquecimento | Em uso (opcional) | Busca URLs externas quando `TAVILY_API_KEY` existe |

---

## 12. Frontend

| Tecnologia | Camada | Status | Por quê |
|---|---|---|---|
| Next.js (App Router) | `apps/web/app/` | Em uso | Páginas + BFF (`app/api/radar/`) que encaminha ao FastAPI |
| React 19 + TypeScript | `apps/web/features/`, `lib/api/` | Em uso | Componentes e tipos alinhados ao contrato HTTP |
| TanStack Query | `providers/query-provider.tsx` | Em uso | Polling de jobs sem reimplementar cache/retry |
| Tailwind CSS | toda `apps/web/` | Em uso | Utilitários de CSS, sem framework de componentes |
| Vitest + Testing Library | `apps/web/**/*.test.tsx` | Em uso | 32 testes de frontend |
| SVG/HTML em React | `features/dashboard/portfolio-charts.tsx` | Em uso | Gráficos do dashboard sem dependência de chart lib |
| `react-markdown` + `remark-gfm` | `components/markdown-content.tsx` | Em uso | Briefing/justificativa/chat com links clicáveis na tela |

---

## 13. Chaves de API externas (todas opcionais)

```txt
GEMINI_API_KEY       LLM: agentes, classificação, extração, embeddings, prosa, RAG answer
COHERE_API_KEY       reranking do RAG
TAVILY_API_KEY       busca externa para enriquecimento
LANGFUSE_*           tracing/observabilidade de LLM
FIRECRAWL_API_KEY    previsto; client real ainda não implementado
```

Sem qualquer uma delas o sistema continua funcionando, com degradação graciosa.

---

## Como manter este arquivo

Quando uma tecnologia "Candidata" de um `docs/<modulo>/roadmap.md` for
implementada, troque só a coluna Status para "Em uso" — a explicação detalhada
continua no roadmap do módulo.
