# Mapa de Tecnologias

Criado em 23/06/2026. Lista cada tecnologia do projeto — em uso hoje ou
candidata registrada em algum `docs/<modulo>/roadmap_<modulo>.md` — com
onde ela entra na arquitetura e por que. "Em uso" foi confirmado por import
real no codigo nesta auditoria, nao por suposicao a partir de docs.

Regra geral de leitura (do `CLAUDE.md`, "PRE-DECISION CHECKLIST"):

```txt
domain/         nunca importa nenhuma tecnologia de infraestrutura
application/    nunca importa framework externo (so tipos/portas proprias)
infrastructure/ e' onde toda tecnologia concreta (SQLAlchemy, Playwright,
                LangChain, Qdrant client, etc.) realmente vive
factories/      e' o unico lugar que conhece qual implementacao concreta
                usar para cada porta
graphs/         (so em agents) usa LangGraph, e pode importar
                application/+domain/, nunca infrastructure de outro modulo
```

Cada tabela abaixo segue esse padrao: a coluna "Camada" diz onde a
tecnologia entra, nunca em `domain/`.

---

## 1. Transversal / infraestrutura

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| Python 3.13 | runtime de toda a API e workers | Em uso | Linguagem base do projeto |
| FastAPI | `presentation/` de todos os modulos | Em uso | Framework HTTP; nunca aparece em `domain/`/`application/` (regra 2) |
| SQLAlchemy (async) | `infrastructure/database/` de todos os modulos com persistencia | Em uso | ORM; confinado a infra para manter `domain/` puro (regra 5) |
| PostgreSQL | banco relacional, toda tabela do projeto | Em uso | Fonte da verdade (regra 7) — status, auditoria, relacionamentos |
| Alembic | migrations, raiz do projeto | Em uso | Versionamento de schema acompanhando cada entrega |
| Qdrant | `infrastructure/qdrant/` (modulo `embeddings`) | Em uso | Busca por similaridade semantica; todo vetor referencia um ID real do Postgres (regra 7), nunca guarda dado canonico so no Qdrant |
| Redis | broker do Dramatiq (`shared/queue/dramatiq_broker.py`) | Em uso | Fila assincrona compartilhada por todos os workers |
| Dramatiq | toda fila assincrona (5 workers) | Em uso | Mensagens carregam so `job_id`/`run_id` (regra 3); retry/backoff nativo |
| Langfuse (self-hosted, v3) | `shared/observability/`, plugado nos clients LangChain | Em uso | Tracing de chamadas LLM (custo, latencia, prompt/resposta) sem reescrever prompts ou grafos |
| Docker Compose (`infra/docker-compose.yml`) | Postgres/Redis/Qdrant/Langfuse locais | Em uso | Ambiente de desenvolvimento reproduzivel; sem Dockerfile para API/workers ainda (P2 de producao) |

---

## 2. Scraping

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| BeautifulSoup | `infrastructure/scrapers/` | Em uso | Estrategia para paginas estaticas (1a tentativa) |
| Playwright | `infrastructure/scrapers/` | Em uso | Estrategia para paginas com JavaScript pesado |
| Trafilatura | `infrastructure/scrapers/` | Em uso | Isola conteudo principal em paginas densas (artigos, docs tecnicos) |
| httpx (Gemini via HTTP direto) | `infrastructure/semantic_validators/` | Em uso | Validacao semantica leve (LLM_REVIEW) sem trazer LangChain so para isso |
| Firecrawl | — | Candidata (so comentada hoje, `FIRECRAWL_API_KEY` existe em `Settings` sem uso) | Ultimo fallback pago para paginas que esgotam BS4/Playwright/Trafilatura (ex: `rapids-docs` no NVIDIA Knowledge V2) — ver `docs/scraping/roadmap_scraping.md` |

---

## 3. Ingestion

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| (nenhuma lib externa) | `application/text_chunker.py`, `text_cleaner.py` | Em uso | Implementacao manual hoje (split por paragrafo/sentenca/palavra) |
| `langchain_text_splitters` | `application/text_chunker.py` (atras do mesmo contrato) | Candidata | LangChain ja e dependencia direta do projeto (via `agents`/`embeddings`); chunking que respeita estrutura (titulos/listas) sem lib nova — ver `docs/ingestion/roadmap_ingestion.md` |

---

## 4. Embeddings

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| `langchain_google_genai` (`GoogleGenerativeAIEmbeddings`) | `infrastructure/gemini/` | Em uso | Implementa o contrato publico `EmbeddingService`; modelo atual `models/gemini-embedding-001` |
| `qdrant-client` (`AsyncQdrantClient`) | `infrastructure/qdrant/` | Em uso | Upsert/busca de vetores; cria colecao idempotente na primeira chamada |
| hash (SHA-256, stdlib) | candidata em `infrastructure/` | Candidata | Cache por `content_hash` do chunk para nao rechamar Gemini em texto identico — ver `docs/embeddings/roadmap_embeddings.md` |

---

## 5. Agents

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| LangGraph | `graphs/` (7 grafos) | Em uso | Orquestra os nodes de cada agente; nunca aparece em `application/`/`domain/` (regra "LangGraph orquestra, modulos especializados executam") |
| LangChain (`langchain_core`, `ChatGoogleGenerativeAI`) | `infrastructure/llm/` (6 clients) | Em uso | Integra o modelo Gemini aos nodes do grafo |
| Pydantic | saida de todo LLM client | Em uso | Regra 9 — resposta do LLM validada estruturalmente, nunca confiada direto |
| PostgreSQL (checkpoints) | `infrastructure/checkpoints/postgres_checkpointer.py` | Em uso | Persiste estado do LangGraph por `thread_id` (human-in-the-loop, V6/V7) |
| `asyncio.timeout` (stdlib) | `application/use_cases/execute_agent_job.py` | Candidata | Aplicar o limite que o `CLAUDE.md` ja declara obrigatorio (`timeout_total`) mas que ainda nao esta no codigo |
| Tavily | novo `SearchExecutorPort` em `infrastructure/search_adapters/` | Candidata | Unico jeito de transformar a query de texto do Search Planner Agent numa URL real; free tier, integra direto com LangChain — ver `docs/agents/roadmap_agentes.md` |

---

## 6. RAG

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| PostgreSQL full-text search (`to_tsvector`/`ts_rank`) | `infrastructure/database/postgres_lexical_search_repository.py` | Em uso | Busca lexical sem carregar chunks em memoria Python (decisao deliberada contra `rank-bm25`) |
| Cohere (`cohere.AsyncClient.rerank`) | `infrastructure/reranking/` | Em uso | Reordena candidatos por relevancia; degrada graciosamente sem `COHERE_API_KEY` |
| Ragas | `tests/integration/test_ragas_quality_baseline.py` | Em uso (opt-in via `RUN_RAGAS_EVAL=1`) | Mede faithfulness/relevancy/precision/recall contra conteudo real do NVIDIA Knowledge |
| `pg_search` (ParadeDB) | troca de imagem Postgres + nova `LexicalSearchRepository` | Candidata, bloqueada por medicao | So entra se `context_recall` (hoje 0.67) confirmar que `ts_rank` e o gargalo — ver Fase 3 de `docs/roadmap_evolucao_tecnica_mvp.md` |

---

## 7. NVIDIA Knowledge

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| (catalogo estatico em codigo) | `infrastructure/static_catalog/` | Em uso | 18 tecnologias/programas, sem migration — dado nao muda com frequencia que justifique tabela |
| script de health-check (HTTP HEAD, sem lib nova) | novo, `infrastructure/` | Candidata | Detectar fontes do registry que saíram do ar antes de tentar reingerir — ver `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` |
| Extraction Agent (`agents`, reuso) | — | Candidata | Metadados tecnicos da V3 via contrato publico ja existente, em vez de parser novo |

---

## 8. Startups

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| (sem lib externa) | `application/use_cases/`, `domain/entities.py` | Em uso | Modelo relacional + casos de uso simples |
| `rapidfuzz` | `application/use_cases/create_startup.py` | Candidata | Dedup leve por nome/website antes de criar `Startup` duplicada — sem infra de entity resolution pesada (Dedupe.io/Splink), volume nao justifica — ver `docs/startups/roadmap_startups.md` |

---

## 9. Recommendations

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| `re` (regex, stdlib) | `domain/policies.py::_contains_term()` | Em uso | Word-boundary matching (fix do bug de 23/06/2026: substring puro casava "agent" em "agentes") |
| `rag.application.public.question_answerer` (reuso) | novo adapter em `infrastructure/rag_adapters/` | Candidata | Fundamenta a justificativa de cada recomendacao em conteudo NVIDIA real via citacoes, em vez de template fixo — ja e contrato publico existente, zero tech nova |
| `embeddings.application.public.vector_repository` (reuso) | novo adapter | Candidata | Fallback semantico quando keyword match nao encontra nada (setor fora do catalogo) |

---

## 10. Briefing

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| (string/Markdown puro) | `domain/policies.py::build_briefing_markdown()` | Em uso | Saida determinística, sem dependencia de template engine |
| `weasyprint` + Jinja2 | novo, `infrastructure/` | Candidata | Exportacao PDF (V3) a partir do mesmo Markdown — libs leves, sem servico externo de PDF-as-a-service |

---

## 11. Orchestration

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| Dramatiq + Redis (reforco do item 1) | `infrastructure/queue/dramatiq_url_ingestion_dispatcher.py` | Em uso | A propria fila `url_ingestion` funciona como loop de polling (`UrlIngestionStillProcessingError` + reentrega) — decisao deliberada contra Kafka/RabbitMQ (regra 8) |
| Tavily + Search Planner Agent (reuso, ver secao 5) | novo branch em `application/use_cases/advance_url_ingestion_job.py` | Candidata | Chain de enriquecimento: busca novas URLs quando `founders`/`funding_stage`/`customers` ficam vazios apos `try_extract` — ver `docs/orchestration/roadmap_orchestration.md` |

---

## 12. Frontend

| Tecnologia | Camada | Status | Por que |
|---|---|---|---|
| Next.js (App Router) | `apps/web/app/` | Em uso | Paginas + BFF (`app/api/radar/`) que encaminha para o FastAPI |
| React 19 + TypeScript | `apps/web/features/`, `lib/api/` | Em uso | Componentes e tipos compartilhados com o contrato HTTP do backend |
| TanStack Query | `providers/query-provider.tsx` | Em uso | Polling de jobs or (`/jobs/[jobId]`) sem reimplementar cache/retry |
| Tailwind CSS | estilo de toda `apps/web/` | Em uso | Utilitarios de CSS, sem framework de componentes adicional |
| Vitest + React Testing Library | novo, `apps/web/**/*.test.tsx` | Candidata, prioridade alta | Zero testes hoje; 1 bug real de Rules of Hooks ja confirmado em `StartupDetails` — ver `docs/frontend/roadmap_frontend.md` |

---

## Como manter este arquivo atualizado

Sempre que uma "Tecnologia candidata" de algum `docs/<modulo>/
roadmap_<modulo>.md` for implementada, mover a linha correspondente aqui
de "Candidata" para "Em uso" (mesma linha, so trocar a coluna Status) — nao
duplicar a explicacao, que continua vivendo no roadmap do modulo.
