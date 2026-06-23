# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Authoritative Current State (2026-06-23)

Use this section as the source of truth when older historical sections below
disagree.

Implemented:

```txt
Scraping V8
Agents V12 (+ Startup Classifier Agent, Extraction Agent V8, NVIDIA RAG Agent V10, Recommendation Agent V11, Briefing Agent V12 — all 8 agents from the original brief now implemented)
Ingestion V1 + ingestion_worker
Embeddings V5 + embedding_worker
Startups V2 + V3 (slices iniciais: campos estruturados + classificacao de maturidade em IA)
RAG V4 (busca hibrida + reranking)
NVIDIA Knowledge V1
NVIDIA Knowledge V2 foundation + source registry + first real end-to-end validation (2/8 P0 sources)
Recommendations V1
Briefing V1
Orchestration V1 + V2 completa (URL bruta -> scraping -> ingestion -> embeddings -> startup -> evidencia -> extract -> classify -> recommendations -> briefing, sem operacao manual entre etapas) + orchestration_worker automatico
```

MVP macro backlog (`docs/roadmap_proximos_passos.md`) is complete, and the
top case-brief gap (Startup Classifier, see diagnostic doc) is closed too:
scraping -> ingestion -> embeddings -> startups -> rag -> recommendations ->
briefing -> orchestration all implemented, plus Agents V9 + Startups V3
(AI-native/AI-enabled/Non-AI classification). Orchestration V2 P0 #1
(`docs/roadmap_produto_final.md`) is also closed: a raw URL now produces a
briefing and recommendations end to end automatically.

Pending:

```txt
Frontend (apps/web existe localmente com V1+V2, ainda nao commitado/
documentado formalmente nesta secao - ver docs/frontend/)
Auth
Production observability (foundation exists: shared/logging + shared/
observability + Langfuse self-hosted via infra/docker-compose.yml,
mas sem metricas/alertas/retencao de producao)
Recommendations V2/V4 - aprofundar ai_maturity_level no score (bonus
deterministico inicial entregue 23/06/2026 - ver match_technologies()),
RAG com citacoes, prioridade/confianca/complexidade ainda faltam
```

Recent validation:

```txt
474 passed (Postgres/Redis/Qdrant locais ativos)
Integration tests are skipped explicitly when local Postgres/Redis/Qdrant
are not reachable; with infra active, they run normally.

NVIDIA Knowledge V2 first real run against live infra: 2/8 P0 sources
completed end-to-end (scraping -> ingestion -> embeddings), content
retrievable via /rag/search filtered by source_type=nvidia_knowledge.
Fixed 4 bugs found in the process (3 in scraping: captcha false positive,
Playwright stdio/Dramatiq conflict, evidential validation wrongly applied
to curated sources; 1 in embeddings: deprecated Gemini embedding model).
See docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md.
Known unresolved: intermittent hostname resolution failures from the
Windows-side Python process (not WSL) for some domains — environment
networking issue, not a code bug.

Recommendations bug found and fixed testing the real URL flow end-to-end
(https://dadosfera.com.br): match_technologies() used substring puro sem
word boundary, casando "agent" dentro de "agentes" (portugues) e "scale"
dentro de "escale" via alias - 5 recomendacoes saiam todas em 27% por
coincidencia linguistica, nao sinal real. Corrigido com regex \b...\b;
Extraction Agent (agents) ganhou sector/description (sempre em ingles,
para casar com o vocabulario do catalogo NVIDIA), antes nunca escritos
pelo fluxo automatico de URL. Validado: mesma URL agora produz 2
recomendacoes com scores diferenciados (43%/27%) em vez de 5 uniformes.
Ver docs/diagnostico_fraquezas_e_tecnologias_recomendadas.md e
docs/roadmap_evolucao_tecnica_mvp.md.

Observabilidade: shared/logging/ (logger JSON + bind_context() via
contextvars + log_job(), aplicado nos 5 workers e em
AdvanceUrlIngestionJob) e shared/observability/ (get_langfuse_callbacks(),
plugado nos 7 clients LangChain/Gemini) sao codigo novo e real - antes
desta entrega, 1 unico arquivo em todo apps/api/src/modules/ usava
logging, e nenhuma chamada LLM tinha tracing. Langfuse self-hosted (v3,
6 servicos: web/worker/postgres/clickhouse/redis/minio) roda via
infra/docker-compose.yml; validado com trace real capturado de uma
chamada de extracao Gemini.
```

Next recommended implementation:

```txt
Orchestration V2 P0 #1 (docs/roadmap_produto_final.md) is now closed:
AdvanceUrlIngestionJob gained an ANALYZING status between EMBEDDING and
COMPLETED that runs, in a single synchronous pass, create/associate
Startup -> attach evidence -> try_extract/try_classify (best-effort) ->
recommendations.generate() -> briefing.generate(). Jobs with
source_type != "startup_evidence" (e.g. nvidia_knowledge) still complete
right after embedding, unchanged. `startups` gained its first 4 public
contracts beyond StartupProfileReader (StartupCreator, EvidenceAttacher,
ExtractionTrigger, ClassificationTrigger) so orchestration never reaches
into startups' internals. See
docs/orchestration/orchestration_v2_jornada_completa.md.

Remaining P0/P1 from docs/roadmap_produto_final.md: commit/sync frontend
(apps/web V1+V2 exist locally, P0 #2); finish NVIDIA Knowledge V2's
remaining P0/P1/P2 sources (P1 #3); Recommendations V2/V4 — RAG context
with citations, priority/confidence/complexity, integrate Recommendation
Agent V11 into the main path (P1 #4); Briefing export + human review,
integrate Briefing Agent V12 (P1 #5). None of Agents V10/V11/V12 has a
synchronous consumer yet — reachable only via the generic `agent_runs`
queue; the
automatic orchestration flow uses the deterministic
recommendations/briefing generators (V1), not the agents. P2 observability
has a real foundation now (structured logging + Langfuse tracing, see
"Recent validation" above); auth, CI/CD and deploy remain fully open. P3
(case differentiator, demo) remains fully open.
```

Relevant docs:

```txt
docs/diagnostico_case_original_e_novas_prioridades.md
docs/estado_atual_do_projeto.md
docs/roadmap_proximos_passos.md
docs/proximos_passos_mvp.md
docs/rag/roadmap_rag.md
```

---

## Conversation style

End every response to the user with: **bora bill**

---

## PRE-DECISION CHECKLIST — READ BEFORE ANY CODE CHANGE

Before writing, editing, or proposing any code, run through this checklist mentally. If any item is violated, stop and redesign.

### 1. Am I respecting module boundaries?
- No module imports the internals of another module (no importing another module's models, repositories, or services directly).
- Cross-module calls happen only through `application/public/` contracts.
- Example correct: `scraping` calls `agents/application/public/semantic_investigator.py`.
- Example wrong: `scraping` imports `agents/graphs/evidence_validation/graph.py`.

### 2. Am I respecting the dependency direction?
```
presentation → application → domain
infrastructure → domain  (implements ports)
infrastructure → application  (implements ports)
factories → all layers  (only place that knows concrete types)
worker → factory or application/public  (never business logic inside worker)
```
- `domain` must never import from SQLAlchemy, FastAPI, LangGraph, Gemini, or any infrastructure library.
- `application` must never import from Playwright, BeautifulSoup, SQLAlchemy, LangGraph, or any external framework.
- `graphs/` (LangGraph) may import from `application` and `domain`, but not from another module's internals.

### 3. Is the queue message carrying only an ID?
- Queue messages must carry only `job_id` or `run_id` — never full documents or large payloads.
- Workers fetch data from PostgreSQL using the ID.
- Wrong: sending `agent_name + payload` in the queue message.
- Right: sending only `run_id`; all details live in `agent_runs` table.

### 4. Does the worker contain zero business logic?
- Workers do exactly two things: receive an ID from the queue and call the module's factory/use case.
- No prompts, no graph nodes, no scraping logic, no validation rules inside a worker.

### 5. Is the domain layer pure?
- Domain entities enforce status transitions (e.g., `pending → running → completed/failed`).
- Domain enums, exceptions, and value objects live in `domain/`.
- Policies (e.g., acceptance thresholds) live in `domain/policies.py`.
- No framework imports allowed in `domain/`.

### 6. Am I calling LLM/agents only when deterministic validation is insufficient?
- Rule: code validates technical quality, code validates textual quality, LLM/agent validates semantic uncertainty only.
- LLM is called only when `0.45 ≤ quality_score < 0.75` (the ambiguous band).
- Never call LLM for clearly bad content (`< 0.45`) — try fallback scraper or reject.
- Never call LLM when content is clearly good (`>= 0.75`) — accept directly.

### 7. Is PostgreSQL the source of truth?
- Every vector in Qdrant must reference a real record in PostgreSQL by ID.
- Never store the canonical copy of structured data only in Qdrant.
- Status, audit trail, relationships, and history → PostgreSQL.
- Semantic similarity search → Qdrant.

### 8. Am I building only what is needed right now?
- Check the roadmap section below. Do not build future phases before the current phase is solid.
- Do not create agents, modules, or tables that have no immediate use case.
- Directories are created only when a real feature needs them.

### 9. Are prompts validated structurally?
- LLM responses must be validated via Pydantic, enums, or domain policies.
- The prompt is not the only safety net; the system must enforce structure on the output.
- Prompt injection: treat all web-scraped content as untrusted data, never as system instructions.

### 10. Are logs carrying correlation IDs?
- Every log must include the relevant IDs: `request_id`, `job_id`, `startup_id`, `document_id`, `agent_run_id`.
- Never log secrets, API keys, or full sensitive documents.

---

## Project overview

**NVIDIA Startup AI Radar** — a pipeline that collects public data about AI startups, processes it, and generates structured NVIDIA technology recommendations with justifications. The output is an executive briefing per startup.

The system identifies whether a startup is AI-native, AI-enabled, or Non-AI, then matches it to the right NVIDIA technologies (NIM, TensorRT-LLM, Triton, RAPIDS, Riva, MONAI, etc.).

### Full pipeline (in order)
```
User query / URL input
→ Search Planner (what to fetch)
→ Scraping (collect raw content)
→ Deterministic validation (technical + textual)
→ Quality scoring
→ Decision: ACCEPT | LLM_REVIEW | AGENT_REVIEW | FALLBACK | REJECT
→ Semantic validation via LLM (only for ambiguous band)
→ Agent investigation (only when LLM is insufficient)
→ Ingestion (clean, normalize, extract, chunk)
→ PostgreSQL (structured data, source of truth)
→ Embedding → Qdrant (vectors)
→ Hybrid search (lexical BM25/PG full-text + semantic Qdrant)
→ Reranking (Cohere or cross-encoder)
→ RAG (context assembly + LLM response with citations)
→ Startup classification (AI-native / AI-enabled / Non-AI)
→ Evidence validation
→ NVIDIA Recommendation engine (cross startup profile × NVIDIA tech)
→ Executive briefing
```

### Responsibility separation (most important rule)
```
API       → receives HTTP, validates, creates jobs, returns results
Worker    → receives ID from queue, calls module use case, nothing else
Module    → owns business logic, use cases, domain rules, persistence
Service   → executes a specific business operation
Repository → accesses the database
Scraper   → collects raw content from the web
Ingestion → cleans, normalizes, structures, chunks
RAG       → retrieves context, generates answers with citations
Reranker  → orders retrieved evidence by relevance
Recommendation → generates NVIDIA tech recommendations
Briefing  → formats the final output for humans
```

---

## Tech stack

| Layer | Technology |
|---|---|
| API | Python 3.13 + FastAPI |
| Frontend | Next.js + TypeScript + Tailwind + TanStack Query |
| Relational DB | PostgreSQL |
| Vector DB | Qdrant |
| Queue | Redis + Dramatiq |
| Scraping | BeautifulSoup, Playwright, Trafilatura, Firecrawl |
| LLM orchestration | LangGraph + LangChain |
| LLM provider | Google Gemini (via `ChatGoogleGenerativeAI`) |
| Reranking | Cohere Rerank or cross-encoder |
| Virtual env | `venv/` at repo root (Python 3.13) |

---

## Repository layout

```
apps/
  api/src/
    main.py             ← FastAPI entrypoint
    modules/            ← scraping, ingestion, startups, rag, agents, recommendations
    database/
      relational/       ← SQLAlchemy async session, Base
      vector/           ← Qdrant client
    shared/             ← logging/ (logger JSON + bind_context + log_job),
                          observability/ (get_langfuse_callbacks),
                          queue/dramatiq_broker.py; errors/auth ainda nao existem
    config/             ← all env-var loading
  web/src/              ← Next.js frontend
workers/                ← separate processes; thin delegators only
  scraper_worker/       ← run.py + tasks.py
  ingestion_worker/
  embedding_worker/
  agent_worker/
  orchestration_worker/ ← consome fila url_ingestion, avanca UrlIngestionJob
packages/
  shared/               ← cross-process DTOs, event types, constants
  prompts/              ← versioned prompt files (.md)
infra/                  ← docker-compose.yml and service configs
docs/                   ← architecture and per-module docs
```

**Shared broker location**: `apps/api/src/shared/queue/dramatiq_broker.py` — both scraping and agents use it. Never define the broker inside a module.

---

## Module internal structure

Every module under `apps/api/src/modules/<name>/` follows:

```
presentation/   ← FastAPI routes, schemas, exception handlers
application/    ← use cases, services, ports (interfaces), DTOs
  public/       ← contracts exposed to other modules (ONLY entry point for inter-module calls)
domain/         ← entities, value objects, enums, repository contracts, policies, exceptions
infrastructure/ ← SQLAlchemy models/mappers/repos, scrapers, LLM clients, queue adapters, external APIs
factories/      ← wires all concrete types together (only place that knows implementations)
tests/
  unit/
  integration/
  fixtures/
graphs/         ← (agents module only) LangGraph graph definitions, state, nodes, routers
```

### Dependency rules (strictly enforced)
- `presentation → application → domain` (one direction only)
- `infrastructure → domain` and `infrastructure → application` (implements ports)
- `graphs/ → application` and `graphs/ → domain` (but NOT to another module's internals)
- `factories/` connects all layers (only place that knows all concrete types)
- Workers import only from `factories/` or `application/public/`
- `domain/` must never import from infrastructure, FastAPI, SQLAlchemy, LangGraph, or any framework
- `application/` must never import from Playwright, BeautifulSoup, SQLAlchemy, LangChain, etc.

---

## Module version history

This section is the authoritative record of every version of every module. Update it immediately after each delivery. Never leave it stale.

---

### Scraping module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Scraping basico com BeautifulSoup, job + resultado no banco |
| V2 | Entregue | PostgreSQL real, ScrapingJob/Attempt/Result, repositorios async |
| V3 | Entregue | Redis + Dramatiq, scraper_worker, fila assincrona |
| V4 | Entregue | Playwright para paginas dinamicas com JavaScript |
| V5 | Entregue | Validacao deterministica: tecnica + textual + evidencial |
| V6 | Entregue | Trafilatura como estrategia de extracao de texto |
| V7 | Entregue | Validacao semantica com Gemini (LLM_REVIEW), fatores por score |
| V8 | Entregue | Integracao com agents via SemanticInvestigator (AGENT_REVIEW) |

**Versao atual: V8 — modulo completo**

Extensao feita durante a primeira validacao real do NVIDIA Knowledge V2
(continua V8, nao e' nova versao — 3 correcoes de bugs encontrados rodando
fontes reais, ver `docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md`):
- `TechnicalValidator._has_captcha_challenge()` — so bloqueia "captcha"
  quando o sinal vem com pouco texto extraido (`< 500 chars`), mesmo
  padrao de `_requires_javascript`; antes bloqueava qualquer pagina que
  so referenciasse uma lib de captcha no JS (ex: GitHub)
- `PlaywrightScraper` restaura `sys.__stdout__`/`sys.__stderr__` durante
  o launch do driver/browser — o Dramatiq substitui esses streams por um
  pipe entre processos cujo `fileno()` nao e' herdavel no Windows para o
  subprocesso que o Playwright cria, causando `[Errno 9] Bad file
  descriptor`
- `ScrapingJob.source_type` (migration `7d4f2a9c6e83`) trafega desde
  `UrlIngestionJob`; `QualityScoringService` ignora a dimensao de
  evidencia para `source_type != "startup_evidence"`
  (`quality_score = technical*0.5 + text*0.5`), e a pipeline pula
  LLM_REVIEW/AGENT_REVIEW inteiramente para esses casos — fontes curadas
  pelo registry (NVIDIA Knowledge) nao precisam "provar evidencia de IA
  de uma startup"
- Testes: 134 (+4 desta extensao)

Tabelas: `scraping_jobs` (+ `source_type`), `scraping_attempts`, `scraping_results`
Worker: `workers/scraper_worker/` — consome fila `scraping`
Testes: 134 (unit + integration)

---

### Agents module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Contrato publico `SemanticInvestigator` + Gemini via HTTP direto |
| V2 | Entregue | `EvidenceValidationGraph` com LangGraph e LangChain |
| V3 | Entregue | `SearchPlanningGraph` (Search Planner Agent) |
| V3.5 | Entregue | `agent_worker` base + `DramatiqAgentDispatcher` |
| V4 | Entregue | `agent_runs` e `agent_steps` persistidos no PostgreSQL |
| V5 | Entregue | Worker executa grafo correto por `agent_type` com output real |
| V6 | Entregue | Checkpoint LangGraph no PostgreSQL + `waiting_human_review` + `ResumeAgentJob` |
| V7 | Entregue | Presentation layer (GET + POST /resume) + interrupt() real em node |
| V8 | Entregue | Extraction Agent |
| V9 | Entregue | Startup Classifier Agent |
| V10 | Entregue | NVIDIA RAG Agent |
| V11 | Entregue | Recommendation Agent |
| V12 | Entregue | Briefing Agent |

**Versao atual: V12 — todos os 8 agentes do brief original implementados**

O que a V8 entregou (entregue depois da V9, desbloqueado pelo Startups V2):
- `AgentType.EXTRACTION` + `ExtractedFundingStage` (enum, vocabulario interno, mesmos valores de `startups.FundingStage`)
- `ExtractionGraph` — copia estrutural de `StartupClassificationGraph` (3 nodes, sem interrupt); implementa o contrato publico novo `ExtractionService` (`application/public/extractor.py`)
- `LangChainGeminiExtractor` (`infrastructure/llm/`) — copia estrutural de `LangChainGeminiStartupClassifier`; prompt instrui explicitamente a nunca inferir/inventar (anti-alucinacao tratada via prompt + schema Pydantic permissivo, nao via validacao extra de codigo)
- `AgentType.EXTRACTION` wired em `ExecuteAgentJob`/`ResumeAgentJob`, mesmo padrao do Startup Classifier (consumidor real chama sincronamente via adapter, nao pela fila)
- `AgentsFactory.create_extraction_service()`
- Testes: 67 unit (+5 desta entrega: 2 grafo, 2 execute_agent_job, 1 resume_agent_job)

Documento da entrega: `docs/agents/agents_v8_extraction_agent.md`.
Contraparte de dados: `docs/startups/startups_v2_campos_estruturados.md` (Startups V2).

O que a V9 entregou:
- `AgentType.STARTUP_CLASSIFIER` + `StartupMaturityLevel` (enum, vocabulario interno, mesmos valores de `startups.AiMaturityLevel`)
- `StartupClassificationGraph` — copia estrutural de `SearchPlanningGraph` (3 nodes, sem interrupt); implementa o contrato publico novo `StartupClassifierService` (`application/public/startup_classifier.py`)
- `LangChainGeminiStartupClassifier` (`infrastructure/llm/`) — copia estrutural de `LangChainGeminiEvidenceJudge`
- `AgentType.STARTUP_CLASSIFIER` wired em `ExecuteAgentJob`/`ResumeAgentJob` (consistencia interna — todo agent_type tem um branch), mas o consumidor real (`startups`) chama o servico sincronamente via adapter, nao pela fila `agent_runs`
- `AgentsFactory.create_startup_classification_service()`
- Testes: 62 unit (+5 desta entrega: 2 grafo, 2 execute_agent_job, 1 resume_agent_job)

Documento da entrega: `docs/agents/agents_v9_startup_classifier.md`.
Contraparte de dados: `docs/startups/startups_v3_classificacao_maturidade.md` (Startups V3).

O que a V10 entregou:
- `AgentType.NVIDIA_RAG` (vocabulario interno, sem equivalente em outro modulo — este agente nao tem "consumidor com vocabulario proprio" como Extraction/Startup Classifier tem em `startups`)
- `NvidiaRagInput`/`NvidiaRagCitation`/`NvidiaRagResult` (`application/dto.py`) + `NvidiaRagToolPort` (`application/ports.py`, porta interna para chamar `rag` como tool)
- `NvidiaRagGraph` (`graphs/nvidia_rag/`) — copia estrutural de `ExtractionGraph` (3 nodes, sem interrupt); implementa o contrato publico novo `NvidiaRagService` (`application/public/nvidia_rag.py`)
- Diferente dos demais agentes: **sem LLM client proprio**. O node `query_rag` chama `RagQuestionAnswererAdapter` (`infrastructure/rag_adapters/`), que implementa `NvidiaRagToolPort` chamando `rag/application/public/question_answerer.py` direto — a geracao de resposta com citacoes ja existe em `rag` V4, reimplementar seria duplicar custo de LLM e violar a regra de nao reimplementar logica de outro modulo
- Mudanca cruzada em `rag` (continua V4, nao e nova versao): novo contrato publico `RagQuestionAnswerer`; `AnswerQuestion` passou a implementar direto (`answer()` tem a logica, `execute()` delega — mesmo padrao de `GenerateRecommendations`/`GenerateBriefing`); `RagFactory.create_question_answerer()`
- `AgentType.NVIDIA_RAG` wired em `ExecuteAgentJob`/`ResumeAgentJob`; `AgentsFactory.create_nvidia_rag_service()` segue a mesma regra dos outros 4 agentes (sem `GEMINI_API_KEY`, devolve `None`)
- Sem consumidor sincrono dedicado ainda (Recommendation Agent V11 e Briefing Agent V12, que vao usa-lo como tool, nao existem); acionavel hoje pela fila generica `agent_runs` com `agent_type=nvidia_rag`
- Testes: 9 unit (+7 em `agents`: 2 adapter, 2 grafo, 2 `execute_agent_job`, 1 `resume_agent_job`; +0 em `rag`, os testes existentes de `AnswerQuestion.execute()` continuam cobrindo a logica movida para `answer()`)

Documento da entrega: `docs/agents/agents_v10_nvidia_rag_agent.md`.

O que a V11 entregou:
- `AgentType.RECOMMENDATION` + `RecommendationAgentInput`/`RecommendationCandidate`/`RecommendationAgentResult` (`application/dto.py`)
- `RecommendationToolPort` (chama `recommendations` como tool) + `RecommendationReviewerPort` (revisao via LLM), ambos em `application/ports.py`
- `RecommendationAgentGraph` (`graphs/recommendation/`) — 4 nodes: `prepare_context -> generate_recommendations -> review_and_enrich -> finalize`; pula a revisao por LLM quando nao ha candidatos
- Primeiro agente com as duas pontas ao mesmo tempo: tool determinística (`RecommendationGeneratorAdapter`, `infrastructure/recommendations_adapters/`, chama `RecommendationsFactory.create_recommendation_generator()` direto) **e** LLM client proprio (`LangChainGeminiRecommendationReviewer`, `infrastructure/llm/`) — diferente do NVIDIA RAG Agent (V10, so tool, sem LLM) e do Extraction/Startup Classifier (V8/V9, so LLM, sem tool cross-modulo)
- Guarda em codigo (regra 9 do CLAUDE.md): candidatos com `score >= 0.5` sao sempre mantidos, mesmo se o LLM tentar descartar; so candidatos ambiguos (`score < 0.5`) tem o `keep`/`discard` do LLM respeitado. Limiar proprio de `agents`, decoupled do `MIN_MATCH_SCORE=0.25` de `recommendations`
- Revisao em lote: uma chamada Gemini por startup (nao uma por recomendacao), julgando ambiguidade e reescrevendo a justificativa em linguagem de negocio de todos os candidatos mantidos
- `AgentType.RECOMMENDATION` wired em `ExecuteAgentJob`/`ResumeAgentJob`; `AgentsFactory.create_recommendation_agent_service()` segue a mesma regra dos outros agentes (sem `GEMINI_API_KEY`, devolve `None`)
- Import circular descoberto e corrigido: `agents -> recommendations -> startups -> agents` (`startups_factory.py` ja importa `AgentsFactory` para os adapters V8/V9); resolvido com import lazy de `RecommendationsFactory` dentro do metodo da factory, mesmo padrao de `nvidia_knowledge_factory.py` chamando `orchestration`
- Sem consumidor sincrono dedicado ainda; acionavel pela fila generica `agent_runs` com `agent_type=recommendation`
- Testes: 13 unit (+2 adapter, +9 reviewer, +2 grafo)

Documento da entrega: `docs/agents/agents_v11_recommendation_agent.md`.

O que a V12 entregou (ultimo dos 8 agentes do brief original — todos
implementados a partir desta entrega):
- `AgentType.BRIEFING` + `BriefingAgentInput`/`BriefingAgentResult` (`application/dto.py`)
- `BriefingToolPort` (chama `briefing` como tool, devolve so o Markdown) + `BriefingProseRewriterPort` (reescrita via LLM), ambos em `application/ports.py`
- `BriefingAgentGraph` (`graphs/briefing/`) — 4 nodes: `prepare_context -> generate_briefing -> rewrite_prose -> finalize`; diferente do Recommendation Agent, `rewrite_prose` nunca e' pulado (reescrever a prosa e' o proposito inteiro do agente, nao uma excecao condicional)
- `BriefingGeneratorAdapter` (`infrastructure/briefing_adapters/`, chama `BriefingFactory.create_briefing_generator()` direto) + `LangChainGeminiBriefingProseRewriter` (`infrastructure/llm/`)
- Fallback seguro em codigo (nao confiado so ao prompt, regra 9): extrai todas as URLs do Markdown deterministico, e se a reescrita do LLM perder alguma, devolve o Markdown original inalterado — mesmo espirito do "code-enforced override" do Recommendation Agent (V11), aplicado dentro da porta, nao no grafo
- `AgentType.BRIEFING` wired em `ExecuteAgentJob`/`ResumeAgentJob`; `AgentsFactory.create_briefing_agent_service()` segue a mesma regra dos outros agentes (sem `GEMINI_API_KEY`, devolve `None`)
- Import lazy de `BriefingFactory` dentro do metodo da factory (mesmo ciclo `agents -> briefing -> startups -> agents` do Recommendation Agent, corrigido preventivamente)
- Sem consumidor sincrono dedicado ainda; acionavel pela fila generica `agent_runs` com `agent_type=briefing`
- Testes: 10 unit (+2 adapter, +7 rewriter, +1 grafo)

Documento da entrega: `docs/agents/agents_v12_briefing_agent.md`.

O que a V6 entregou:
- `PostgresCheckpointer` em `infrastructure/checkpoints/` wraps `AsyncPostgresSaver` (lazy init)
- Grafos aceitam `checkpointer` no `__init__`, compilam com ele na primeira chamada com `thread_id`
- `thread_id = str(run.id)` passado pelo `ExecuteAgentJob` a cada chamada de servico
- `AgentRunStatus.WAITING_HUMAN_REVIEW` — novo status de dominio
- `AgentRun.interrupt(value)` e `AgentRun.resume()` — novas transicoes de estado
- `AgentRunInterruptedError` — excecao de dominio, sem imports LangGraph
- `ExecuteAgentJob` captura `AgentRunInterruptedError` e pausa o run (nao falha)
- `ResumeAgentJob` — novo caso de uso para retomar runs pausados
- Migration `9e1f3b5c8a2d`: tabelas `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`
- Testes: 50 unit (agentes)

O que a V5 entregou (historico):
- `ExecuteAgentJob` recebe `EvidenceValidationService` e `SearchPlanningService` via factory
- Despacha para o grafo correto pelo `agent_type` persistido em `agent_runs`
- Salva output real em `agent_runs.output_payload`
- Salva `AgentStep` real com nome `execute_{agent_type}`
- Falhas do LLM ou do grafo → `run.fail(reason)` → status `FAILED`
- `AgentServiceUnavailableError` quando chave de API esta ausente

Tabelas: `agent_runs`, `agent_steps`, `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`
Worker: `workers/agent_worker/` — consome fila `agents`
Testes: 50 unit

---

### Ingestion module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | TextCleaner, TextChunker, Document, Chunk, worker ingestion_worker |

**Versao atual: V1**

O que a V1 entregou:
- `TextCleaner` — normaliza CRLF, remove chars de controle, colapsa linhas em branco
- `TextChunker` — divide texto em chunks de 2000 chars com overlap de 200, respeitando paragrafos > sentencas > palavras
- Entidades: `IngestionJob`, `Document`, `Chunk` com status transitions
- Casos de uso: `CreateIngestionJob`, `ExecuteIngestionJob`, `GetIngestionJob`
- `ScrapingResultReader` — le scraping_results via SQL textual (sem importar internals do modulo scraping)
- Migration: `ingestion_jobs`, `documents`, `chunks`
- Worker: `workers/ingestion_worker/` — consome fila `ingestion`
- Presentation: `POST /ingestion/jobs` e `GET /ingestion/jobs/{id}`
- Contrato publico: `IngestedDocumentReader` em `application/public/`

Extensao feita durante a entrega do Embeddings V4 (modulo `ingestion` continua V1, isso nao e' uma nova versao, e' so a primeira vez que o contrato publico ganhou implementacao real):
- Novo metodo `list_chunks_by_document_id()` em `IngestedDocumentReader` (`ChunkRecord` como DTO de retorno)
- `PostgresIngestedDocumentReader` (`infrastructure/database/`) — primeira implementacao concreta do contrato (existia desde a V1 mas nunca tinha sido implementado nem usado); SQL textual, mesmo padrao do `PostgresScrapingResultReader`
- `IngestionFactory.create_ingested_document_reader()`

Extensao feita durante o fechamento da Orchestration V2 (continua V1):
`IngestedDocumentSummary` ganha `clean_text: str = ""` — primeira vez que
o texto limpo do documento (nao so os chunks) e exposto via contrato
publico; `orchestration` usa para nomear a startup criada e como conteudo
da evidencia anexada.

Tabelas: `ingestion_jobs`, `documents`, `chunks`
Worker: `workers/ingestion_worker/` — consome fila `ingestion`
Testes: 33 unit + 1 integracao (novo, exige Postgres real rodando)

---

### Embeddings module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Contrato publico `EmbeddingService`, DTOs, `GenerateChunkEmbedding`, provider fake deterministico |
| V2 | Entregue | Provider real (Gemini) por tras do mesmo contrato |
| V3 | Entregue | Persistencia no Qdrant (`VectorRepository`, upsert, busca) |
| V4 | Entregue | Worker em batch (`workers/embedding_worker`, fila `embeddings`), `EmbeddingJob`/`EmbeddingJobChunk`, retry/backoff via Dramatiq |
| V5 | Futuro | Reembedding e metricas |

**Versao atual: V4**

O que a V1 entregou:
- `EmbeddingVector` — value object imutavel (`domain/entities.py`), valida `len(values) == dimension`
- `EmbeddingsError`, `EmptyChunkTextError`, `InvalidEmbeddingDimensionError` — excecoes de dominio
- DTOs: `GenerateChunkEmbeddingInput`, `ChunkEmbeddingView`
- Contrato publico: `EmbeddingService` em `application/public/embedding_service.py` (unico arquivo que outros modulos podem importar)
- Caso de uso `GenerateChunkEmbedding` — valida texto vazio e delega ao `EmbeddingService` injetado
- `DeterministicFakeEmbeddingProvider` — implementacao V1 do contrato (infra), gera vetor estavel via SHA-256 do texto, sem chamar API externa
- `EmbeddingsFactory` — composicao das dependencias

Sem banco, sem Qdrant, sem worker, sem presentation — nada disso tinha referente em V1 (decisao deliberada, ver `docs/embeddings/roadmap_embeddings.md`). `GenerateChunkEmbedding` (use case) e `DeterministicFakeEmbeddingProvider` (infra) sao classes separadas — o use case nunca implementa o contrato publico diretamente, mesmo padrao do `EvidenceValidationService` em `agents`. Isso evitou um refactor forcado quando a V2 trocou o provider fake por um real.

O que a V2 entregou:
- `GeminiEmbeddingProvider` (`infrastructure/gemini/`) — implementacao real do `EmbeddingService` via `GoogleGenerativeAIEmbeddings` (LangChain), `embedding_client` injetavel para testes sem rede
- `EmbeddingServiceUnavailableError`, `EmbeddingGenerationError` — novas excecoes de dominio
- `EmbeddingsFactory.create_embedding_service()` devolve `None` sem `GEMINI_API_KEY` configurada — sem fallback silencioso para o fake; `GenerateChunkEmbedding.execute()` levanta `EmbeddingServiceUnavailableError` so na hora do uso real (mesmo padrao do `AgentServiceUnavailableError` em `agents`)
- Setting nova: `gemini_embedding_model` (default `models/text-embedding-004`)

O que a V3 entregou:
- DTOs: `UpsertChunkEmbeddingInput`, `ChunkEmbeddingRecord`, `ChunkSearchResult`
- Contrato publico: `VectorRepository` em `application/public/vector_repository.py` (upsert + search) — publico desde ja porque o RAG futuro vai chamar `search()` direto
- Caso de uso `UpsertChunkEmbedding` — compoe `GenerateChunkEmbedding` + `VectorRepository`
- `QdrantVectorRepository` (`infrastructure/qdrant/`) — usa `AsyncQdrantClient`; cria a colecao de forma idempotente no primeiro upsert, usando a dimensao do vetor inserido
- Setting nova: `qdrant_collection_name` (default `chunk_embeddings`); dependencia nova: `qdrant-client>=1.12,<2`
- Erros do client do Qdrant nao sao empacotados em excecao de dominio — mesmo padrao dos repositorios Postgres existentes

O que a V4 entregou:
- `EmbeddingJob` + `EmbeddingJobChunk` (`domain/entities.py`) — par "job + filhos" igual `AgentRun`/`AgentStep`, status agregado (`PENDING/RUNNING/COMPLETED/PARTIAL/FAILED`) e status por chunk (`PENDING/COMPLETED/FAILED`)
- Retry sem scheduler customizado: `EmbeddingJobChunk.record_failure()` incrementa `attempt_count` e so fica `FAILED` (terminal) ao atingir `MAX_CHUNK_ATTEMPTS=3`; enquanto isso fica `PENDING`. `ExecuteEmbeddingJob` levanta `EmbeddingJobPartiallyFailedError` quando sobra chunk pendente, e o Dramatiq (`max_retries=3`, mesmo valor de todos os workers) reentrega a mensagem — so reprocessa os chunks ainda pendentes (idempotente, mesmo padrao de guarda do `ExecuteScrapingJob`)
- Cada chunk e' salvo (e comitado) individualmente durante o loop, nao numa transacao unica presa durante N chamadas de rede sequenciais
- Mudanca no modulo `ingestion` (entrega cruzada, ver secao do modulo ingestion): novo metodo `list_chunks_by_document_id()` no contrato publico `IngestedDocumentReader`, e a primeira implementacao concreta (`PostgresIngestedDocumentReader`) — o contrato existia desde a V1 do ingestion mas nunca tinha sido implementado
- `IngestionChunkReader` (`infrastructure/ingestion_adapters/`) — adapter que implementa a porta interna `ChunkSourceReader` embrulhando o contrato publico do ingestion; `EmbeddingsFactory` importa `IngestionFactory` direto e chama `create_ingested_document_reader()` (mesmo padrao de `scraping_factory.py` chamando `AgentsFactory`)
- Casos de uso `CreateEmbeddingJob`, `ExecuteEmbeddingJob`, `GetEmbeddingJob`; dispatcher Dramatiq (`DramatiqEmbeddingJobPublisher`/`DramatiqEmbeddingTaskDispatcher`)
- Migration `b7e2c4f8a1d3`: tabelas `embedding_jobs`, `embedding_job_chunks` (FK cross-modulo no nivel do banco para `documents.id`/`chunks.id` — permitido; import de classes Python entre modulos e' que e' proibido)
- Worker: `workers/embedding_worker/` — consome fila `embeddings`
- Presentation: `POST /embeddings/jobs` e `GET /embeddings/jobs/{id}`

Limite conhecido: se um chunk falhar persistentemente e o job tambem esgotar as 3 entregas do Dramatiq antes do chunk atingir seu proprio teto de tentativas, o job fica em RUNNING sem mais progresso automatico — aceitavel para um worker "basico" (V4); nao resolvido agora.

Tabelas: `embedding_jobs`, `embedding_job_chunks`
Worker: `workers/embedding_worker/` — consome fila `embeddings`
Testes: 56 unit + 2 integracao (exigem Postgres e Qdrant reais rodando)

Extensao feita durante a primeira validacao real do NVIDIA Knowledge V2
(continua V4, nao e' nova versao): `GEMINI_EMBEDDING_MODEL` default
trocado de `models/text-embedding-004` (descontinuado pela API do
Gemini, devolvia 404 em `embedContent`) para `models/gemini-embedding-001`
(3072 dimensoes, validado com chamada real). Sem migracao de dados — a
colecao Qdrant local estava vazia. Ver
`docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md`.

---

### Startups module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Modelo relacional basico (`Startup`, `StartupEvidence`) |
| V2 | Entregue (slice inicial) | Campos estruturados (founders/funding/customers) |
| V3 | Entregue (slice inicial) | Classificacao de maturidade em IA |
| V4 | Futuro | Auditoria e confianca |

**Versao atual: V3 (slice inicial)**

O que a V1 entregou: ver `docs/startups/startups_v1_modelo_relacional.md`.

Extensao feita durante a entrega do Recommendations V1 (continua V1):
primeiro contrato publico do modulo, `StartupProfileReader`
(`application/public/`), implementado por `GetStartupProfile`.

O que a V2 entregou (slice inicial — so campos estruturados, sem
deduplicacao/consolidacao multi-fonte, ver limites no documento da
entrega):
- Enum `FundingStage` (`PRE_SEED/SEED/SERIES_A/SERIES_B/SERIES_C_PLUS/UNKNOWN`)
- `Startup` ganha `founders`/`customers` (`tuple[str, ...]`, JSONB NOT NULL default `[]`) e `funding_stage`/`funding_amount_usd` (nullable)
- `Startup.update()` estendido com os 4 campos; valida `funding_amount_usd` negativo
- Migration `f77998c46d08`
- Destino de dados para o futuro Extraction Agent (`agents` V8), agora desbloqueado
- Testes: 24 unit + 1 integracao (+5 unit desta entrega)

Documento da entrega: `docs/startups/startups_v2_campos_estruturados.md`.

O que a V3 entregou (slice inicial — nao cobre os 4 itens do roadmap
original, ver limites na secao do documento da entrega):
- `AiMaturityLevel` (enum: `AI_NATIVE`/`AI_ENABLED`/`NON_AI`), mesmos valores de `agents.StartupMaturityLevel`
- 3 colunas novas em `startups` (`ai_maturity_level`, `classification_reason`, `classified_at`) via `ALTER TABLE` — atributo 1:1 do `Startup`, nao entidade separada
- `Startup.classify(level, reason)` — metodo de dominio
- `StartupClassifierPort` (`application/ports.py`, primeiro arquivo de ports deste modulo) + adapter `AgentsStartupClassifier` (`infrastructure/agent_adapters/`) chamando `agents` sincronamente (mesmo padrao de `AgentsSemanticInvestigator` em `scraping`)
- `ClassifyStartup` (use case) — recebe `classifier: StartupClassifierPort | None`; levanta `StartupClassificationUnavailableError` (503) so no uso, quando `agents` nao tem `GEMINI_API_KEY`
- `POST /startups/{id}/classify`
- Migration `3ca1a725713e`
- Testes: 21 unit + 1 integracao (+5 unit desta entrega: 2 entidade, 3 caso de uso)

Documento da entrega: `docs/startups/startups_v3_classificacao_maturidade.md`.

Extensao feita durante o fechamento da Orchestration V2 (continua V3, nao
e' nova versao — primeira vez que o modulo ganha contratos publicos alem
de `StartupProfileReader`, ver
`docs/orchestration/orchestration_v2_jornada_completa.md`):
- 4 contratos publicos novos em `application/public/`: `StartupCreator`
  (`create_startup`), `EvidenceAttacher` (`attach_evidence`),
  `ExtractionTrigger` (`try_extract`), `ClassificationTrigger`
  (`try_classify`) — cada um implementado direto pelo use case existente
  (`CreateStartup`, `AddStartupEvidence`, `ExtractStartupProfile`,
  `ClassifyStartup`), mesmo padrao de
  `GenerateRecommendations(RecommendationGenerator)`
- `try_extract`/`try_classify` fazem o swallow de
  `StartupExtractionUnavailableError`/`StartupClassificationUnavailableError`
  (sem `GEMINI_API_KEY`) dentro do proprio modulo — quem chama
  (`orchestration`) nunca precisa conhecer essas excecoes
- Testes: +6 unit (1 `create_startup`, 1 `attach_evidence`, 2
  `try_extract`, 2 `try_classify`)

---

### RAG module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Busca semantica simples |
| V2 | Entregue | Resposta com citacoes |
| V3 | Entregue | Busca hibrida (vetorial + lexical, RRF) |
| V4 | Entregue | Reranking (Cohere Rerank) |
| V5 | Futuro | Avaliacao de qualidade |

**Versao atual: V4**

O que V3 entregou:
- Busca lexical via PostgreSQL full-text search nativo (`to_tsvector('simple', text)` + `websearch_to_tsquery` + `ts_rank`), nao BM25 via lib Python — evita carregar chunks em memoria
- `domain/policies.py::fuse_rankings()` — Reciprocal Rank Fusion (RRF, k=60), funcao pura (primeiro domain deste modulo alem de exceptions.py)
- `PostgresLexicalSearchRepository` — SQL textual contra `chunks` (de `ingestion`), mesmo padrao de `PostgresScrapingResultReader`
- Pool de candidatos `max(limit*4, 20)` antes de fundir/rerankar
- Migration `8d84cba84a02`: indice GIN de expressao em `chunks`
- Mudanca de comportamento: `EvidenceChunkView.score` agora e o score RRF, nao mais o cosine score puro do Qdrant

O que V4 entregou:
- `CohereReranker` (`infrastructure/reranking/`) — `cohere.AsyncClient.rerank()`, `COHERE_API_KEY` (ja existia em `Settings`, nunca usada) finalmente em uso
- Degradacao graciosa (diferente do padrao Gemini/503): sem API key ou com falha em runtime do Cohere, busca segue sem reranking em vez de falhar
- Reranking aplicado dentro de `SearchEvidence.search()` — beneficia `/rag/search` e `/rag/answer`
- Dependencia nova: `cohere>=5.0,<6`
- Testes: 16 unit (+9 desta entrega: 5 `fuse_rankings`, 4 `search_evidence`) + 1 integracao nova

Documentos: `docs/rag/rag_v3_busca_hibrida.md`, `docs/rag/rag_v4_reranking.md`.

---

### NVIDIA Knowledge module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Catalogo inicial de tecnologias (10 itens) |
| V2 | Em andamento | Ingestao de fontes oficiais (pipeline real, nao catalogo estatico) |
| V3 | Futuro | Metadados tecnicos |
| V4 | Futuro | Busca por caso de uso |

**Versao atual: V1 + V2 em andamento**

O que a V1 entregou: `NvidiaTechnology`, catalogo estatico em
`catalog_data.py`, contrato publico `NvidiaTechnologyCatalog`, rotas
`GET /nvidia-knowledge/technologies` e `GET /nvidia-knowledge/technologies/{slug}`.
Ver `docs/nvidia_knowledge/nvidia_knowledge_v1_catalogo_inicial.md`.

Extensao feita apos o diagnostico do case original (continua V1, nao e
nova versao — catalogo e dado estatico em codigo, sem migration):
- 8 tecnologias/programas adicionados (`NVIDIA Inception`, `NeMo Guardrails`, `NVIDIA Clara`, `cuDF`, `cuML`, `NVIDIA Omniverse`, `NVIDIA Isaac`, `NVIDIA Morpheus`) — catalogo cobre os 16 itens do brief original (secao 5.4)
- 3 categorias novas em `NvidiaTechnologyCategory`: `STARTUP_PROGRAM`, `ROBOTICS_SIMULATION`, `CYBERSECURITY`
- `NVIDIA Inception` (o programa de startups que o projeto existe para alimentar) agora e recuperavel pelo catalogo — antes nao tinha nenhuma entrada
- Testes: 7 unit (+2 desta extensao)

Documento: `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` (secao "Extensao do catalogo V1").

O que a V2 (em andamento) entregou — fundacao + registry + primeira
validacao real:
- `documents.source_type` + payload `source_type` no Qdrant + filtro
  opcional em `/rag/search`/`/rag/answer` (ver
  `docs/nvidia_knowledge/nvidia_knowledge_v2_foundation_source_type.md`)
- `NvidiaKnowledgeSourceRegistry` com 20 fontes (8 P0/9 P1/3 P2),
  `GET /nvidia-knowledge/sources`, `POST /nvidia-knowledge/ingestion/jobs`
  (ver `docs/nvidia_knowledge/nvidia_knowledge_v2_source_registry.md`)
- `workers/orchestration_worker/` avancando `url_ingestion_jobs`
  automaticamente (ver `docs/orchestration/orchestration_v2_worker_automatico.md`)
- Primeira ingestao real confirmada ponta a ponta: `nemo-framework-docs`
  e `triton-inference-server-docs` completaram
  `scraping -> ingestion -> embeddings`, conteudo recuperavel via
  `/rag/search` filtrado por `source_type=nvidia_knowledge` — corrigiu 4
  bugs que bloqueavam isso (3 em `scraping`, 1 em `embeddings`; ver
  `docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md`)
- Pendente: re-testar as outras 6 fontes do lote P0 com workers limpos, e
  rodar P1/P2; resolucao de hostname intermitente do lado Windows
  (docs.nvidia.com, docs.monai.io) ainda sem solucao — fora do alcance de
  uma correcao de codigo

Documento: `docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md`.

---

### Recommendations module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Regras deterministicas: cruzamento perfil da startup x catalogo NVIDIA |
| V2 | Futuro | Recomendacao com RAG |
| V3 | Futuro | Agent Recommendation |
| V4 | Futuro | Ranking e confianca |
| V5 | Futuro | Feedback humano |

**Versao atual: V1**

O que a V1 entregou:
- `Recommendation` (`domain/entities.py`) — tecnologia recomendada, score (0-1), justificativa, `matched_keywords` e `evidence_ids` para rastreabilidade
- `domain/policies.py::match_technologies()` — funcao pura: cruza setor/descricao/evidencias da startup com `keywords` de cada tecnologia do catalogo NVIDIA, score = keywords batidas / total; entra na recomendacao com `score >= 0.25` e pelo menos 1 keyword. Sem LLM, sem agente.
- Contrato publico novo em `startups` (nao existia nenhum desde a V1 do modulo): `StartupProfileReader` (`startups/application/public/`), implementado por `GetStartupProfile` direto (mesmo padrao de `ListNvidiaTechnologies(NvidiaTechnologyCatalog)` em `nvidia_knowledge`) — `startups` continua V1, isto e extensao de superficie publica
- `recommendations/application/ports.py` (`StartupProfileSource`, `NvidiaCatalogSource`) + adapters (`infrastructure/startups_adapters/`, `infrastructure/nvidia_adapters/`) — `RecommendationsFactory` importa `StartupsFactory` e `NvidiaKnowledgeFactory` direto, mesmo padrao de `scraping_factory.py` importando `AgentsFactory`
- `GenerateRecommendations` — substitui (`delete_by_startup_id` + `save`) o lote anterior da mesma startup a cada chamada; V1 nao versiona geracoes
- Sem worker/fila: motor de regras so le Postgres + catalogo estatico em codigo, sem I/O externo lento que justifique fila assincrona (mesma categoria de `nvidia_knowledge`, que tambem nao tem worker)
- Migration `f90193dc1578`: tabela `recommendations`
- Presentation: `POST /recommendations`, `GET /recommendations/{id}`, `GET /recommendations?startup_id=`

Tabelas: `recommendations`
Testes: 15 unit + 1 integracao (startups ganhou +2 unit do `GetStartupProfile`)

Documento da entrega: `docs/recommendations/recommendations_v1_regras_deterministicas.md`.

Extensao feita durante a entrega do Briefing V1 (modulo `recommendations` continua V1, isto nao e uma nova versao):
- Novo contrato publico `RecommendationsReader` (`application/public/recommendations_reader.py`) com `list_by_startup_id()`
- `ListRecommendations` passou a implementar o contrato direto (mesmo padrao de `ListNvidiaTechnologies(NvidiaTechnologyCatalog)`); `execute()` agora delega para `list_by_startup_id()`
- `RecommendationsFactory.create_recommendations_reader()`

Extensao feita durante a entrega do Orchestration V1 (continua V1):
- Novo contrato publico `RecommendationGenerator` (`application/public/recommendation_generator.py`) com `generate(startup_id)`
- `GenerateRecommendations` passou a implementar o contrato direto; `execute()` agora delega para `generate()`
- `RecommendationsFactory.create_recommendation_generator()`

Extensao feita em 23/06/2026 (bug fix, continua V1 — ver
`docs/diagnostico_fraquezas_e_tecnologias_recomendadas.md`):
- `ai_maturity_level` passou a entrar no score (`AI_NATIVE_SCORE_BONUS = 0.1`, ja existia desde a extensao anterior, mas estava ausente do Pending da `CLAUDE.md`)
- Bug real encontrado testando `https://dadosfera.com.br`: `match_technologies()` usava substring puro (`keyword in text`), casando `"agent"` dentro de `"agentes"` (portugues) e o alias `"scale"` dentro de `"escale"` — todas as recomendacoes saiam em 27% por coincidencia linguistica. Corrigido com regex `\b...\b` (`_contains_term()`); alias `"scale"` solto removido de `KEYWORD_ALIASES["throughput"]`
- `startups`/`agents`: Extraction Agent (V8) ganhou `sector`/`description` no schema estruturado (sempre em ingles, para casar com o catalogo NVIDIA) — antes, startups criadas pelo fluxo automatico de URL nunca tinham esses campos preenchidos (`orchestration` so usava o `clean_text` para o `name`)
- Validado: mesma URL, antes 5 recomendacoes uniformes em 27%, depois 2 recomendacoes com scores diferenciados (43%/27%)
- Testes: +5 unit (2 `match_technologies`, 2 `extract_startup_profile`, 1 `extraction_graph`)

---

### Briefing module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | Template executivo em Markdown: resumo, evidencias, recomendacoes, riscos e proximas acoes |
| V2 | Futuro | Briefing gerado por agente |
| V3 | Futuro | Exportacao PDF/HTML |
| V4 | Futuro | Revisao humana |
| V5 | Futuro | Ranking de oportunidades |

**Versao atual: V1**

O que a V1 entregou:
- `Briefing` (`domain/entities.py`) — `startup_id`, `content` (Markdown), `generated_at`
- `domain/policies.py` — tres funcoes puras: `assess_risks()` (zero evidencia, evidencia com `confidence_score < 0.5`, zero recomendacao, melhor recomendacao com `score < 0.5`), `suggest_next_actions()` (agenda conversa sobre a melhor tecnologia, ou pede mais evidencias), `build_briefing_markdown()` (monta as 5 secoes). Sem LLM, sem agente.
- Contrato publico novo em `recommendations` (ver secao do modulo recommendations): `RecommendationsReader.list_by_startup_id()`
- `briefing/application/ports.py` (`StartupProfileSource`, `RecommendationsSource`) + adapters (`infrastructure/startups_adapters/`, `infrastructure/recommendations_adapters/`) — `BriefingFactory` importa `StartupsFactory` e `RecommendationsFactory` direto, 5a instancia confirmada do mesmo padrao de wiring cross-modulo desta base
- `GenerateBriefing` — substitui (`delete_by_startup_id` + `save`) o briefing anterior da mesma startup a cada chamada; V1 nao versiona geracoes
- Sem worker/fila: mesma categoria de `nvidia_knowledge`/`recommendations`, so monta uma string a partir de dados ja persistidos
- Migration `782e2cbdbfab`: tabela `briefings`
- Presentation: `POST /briefings`, `GET /briefings/{id}`, `GET /briefings?startup_id=`

Tabelas: `briefings`
Testes: 13 unit + 1 integracao (recommendations ganhou +2 unit do `RecommendationsReader`)

Documento da entrega: `docs/briefing/briefing_v1_template_executivo.md`.

Extensao feita durante a entrega do Orchestration V1 (continua V1):
- Novo contrato publico `BriefingGenerator` (`application/public/briefing_generator.py`) com `generate(startup_id)`
- `GenerateBriefing` passou a implementar o contrato direto; `execute()` agora delega para `generate()`
- `BriefingFactory.create_briefing_generator()`

---

### Orchestration module

| Versao | Status | O que foi entregue |
|---|---|---|
| V1 | Entregue | analysis_jobs a partir de startup_id existente (recommendations -> briefing) |
| V2 | Entregue | Entrada por URL bruta, ponta a ponta: scraping -> ingestion -> embeddings -> startup -> evidencia -> extract -> classify -> recommendations -> briefing |
| V3 | Futuro | Retomada de jobs falhados (retry por etapa) |
| V4 | Futuro | Notificacoes de conclusao |

**Versao atual: V2 — jornada completa URL -> briefing**

Decisao de escopo confirmada com o usuario: V1 assume que scraping,
ingestion, embeddings e evidencias da startup ja foram feitos manualmente
(fluxo atual). Entrada e um `startup_id` existente — orquestrar a partir de
uma URL bruta exigiria um worker novo so para fazer polling de 3 pipelines
assincronas alheias, sem necessidade imediata (fica como Orchestration V2).

O que a V1 entregou:
- `AnalysisJob` (`domain/entities.py`) — ciclo de vida `pending -> running
  -> completed|failed` (`start()`/`complete()`/`fail()`), mesmo padrao de
  `AgentRun`; e um log de execucoes (nao substitui o anterior, diferente de
  `Recommendation`/`Briefing`)
- Contratos publicos novos em `recommendations`
  (`RecommendationGenerator.generate()`) e `briefing`
  (`BriefingGenerator.generate()`) — ver secoes desses modulos
- `orchestration/application/ports.py` (`RecommendationsPort.generate() ->
  int`, `BriefingPort.generate() -> UUID`) — vocabulario simplificado, so o
  que `ExecuteAnalysisJob` precisa para `AnalysisJob.complete()`
- `ExecuteAnalysisJob` — encadeia `RecommendationsPort.generate()` depois
  `BriefingPort.generate()`; sucesso -> `complete(recommendation_count,
  briefing_id)`; excecao -> `fail(reason)` + persiste + relanca (HTTP mapeia
  para 404 quando a startup nao existe)
- `OrchestrationFactory` importa `RecommendationsFactory` e
  `BriefingFactory` direto — 7a e 8a instancia confirmada do mesmo padrao de
  wiring cross-modulo desta base
- Sem worker/fila: as duas etapas encadeadas ja sao sincronas
- Migration `2e85accbd38f`: tabela `analysis_jobs`
- Presentation: `POST /analysis/jobs`, `GET /analysis/jobs/{id}`,
  `GET /analysis/jobs?startup_id=`

Tabelas: `analysis_jobs`
Testes: 9 unit + 1 integracao (recommendations e briefing ganharam +2 unit
cada do `RecommendationGenerator`/`BriefingGenerator`)

Documento da entrega: `docs/orchestration/orchestration_v1_analysis_jobs.md`.

O que a V2 parcial entregou:
- `UrlIngestionJob` com `source_type` e ciclo `pending -> scraping -> ingesting -> embedding -> completed|failed`
- Migration `5b6c7d8e9f01`: tabela `url_ingestion_jobs`
- `CreateUrlIngestionJob`, `GetUrlIngestionJob`, `AdvanceUrlIngestionJob`
- Adapters para `ScrapingJobSubmitter`, `IngestionJobSubmitter` e `EmbeddingJobSubmitter`
- Presentation: `POST /url-ingestion/jobs`, `GET /url-ingestion/jobs/{id}`,
  `POST /url-ingestion/jobs/{id}/advance`
- `POST /nvidia-knowledge/ingestion/jobs` cria `url_ingestion_jobs` com
  `source_type="nvidia_knowledge"` para as fontes oficiais do registry

Documento da entrega parcial: `docs/orchestration/orchestration_v2_url_ingestion_jobs.md`.

Extensao feita depois (continua V2 parcial — fecha o gap do "advance
explicito" deixado pelo slice anterior, ainda nao cobre URL bruta ate
startup/briefing):
- `DramatiqUrlIngestionJobPublisher` + `DramatiqUrlIngestionTaskDispatcher`
  (`infrastructure/queue/dramatiq_url_ingestion_dispatcher.py`) — mesmo
  padrao de `DramatiqEmbeddingJobPublisher`/`DramatiqEmbeddingTaskDispatcher`
  (constroi `dramatiq.Message` direto, sem importar o actor do worker)
- `workers/orchestration_worker/` — consome a fila `url_ingestion`, actor
  `advance_url_ingestion_job`, chama `AdvanceUrlIngestionJob.execute()`;
  `max_retries=50`, backoff 5s-5min (~4h de tentativas automaticas)
- `UrlIngestionTaskDispatchError` (`domain/exceptions.py`)
- `OrchestrationFactory.create_create_url_ingestion_job()` agora publica
  na fila real; `NoopUrlIngestionTaskDispatcher` removido (sem uso)
- A fila e' o proprio loop de polling: o worker levanta
  `UrlIngestionStillProcessingError` (ja existia) e o Dramatiq reentrega a
  mesma mensagem com backoff ate completed|failed
- `POST /url-ingestion/jobs/{id}/advance` continua existindo para
  destravar manualmente um job que esgotou os retries automaticos
- Testes: +3 unit (`test_dramatiq_url_ingestion_dispatcher.py`)

Documento da entrega: `docs/orchestration/orchestration_v2_worker_automatico.md`.

O que a V2 entregou no fechamento final (jornada completa URL -> briefing,
fecha o P0 #1 de `docs/roadmap_produto_final.md`):
- Novo status `ANALYZING` em `UrlIngestionJobStatus`, entre `EMBEDDING` e
  `COMPLETED`; `UrlIngestionJob` ganha `startup_id`, `evidence_attached`,
  `recommendation_count`, `briefing_id` e os metodos
  `start_analyzing()`/`link_startup()`/`mark_evidence_attached()`/
  `record_analysis_result()`
- `AdvanceUrlIngestionJob` ganha o branch `ANALYZING`: roda numa unica
  entrega create/associate `Startup` -> attach evidence -> try_extract +
  try_classify (best-effort) -> recommendations.generate() ->
  briefing.generate(); falha e' terminal (`job.fail()`, sem relancar,
  diferente do padrao "ainda processando" das etapas assincronas
  anteriores); guardas de idempotencia (`startup_id`/`evidence_attached`
  persistidos assim que resolvidos) protegem contra reentrega-por-crash
  do Dramatiq
- Gate por `source_type`: so `"startup_evidence"` entra em `ANALYZING`;
  qualquer outro valor (`nvidia_knowledge` etc) completa direto ao fim do
  embedding, como antes (allow-list deliberada)
- 4 contratos publicos novos em `startups/application/public/`
  (`StartupCreator`, `EvidenceAttacher`, `ExtractionTrigger`,
  `ClassificationTrigger`), implementados direto pelos use cases
  existentes — antes desta entrega `startups` so tinha
  `StartupProfileReader`
- `IngestedDocumentSummary` (`ingestion`) ganha `clean_text: str = ""`
- `StartupsPort` novo em `orchestration/application/ports.py`;
  `IngestionPort` ganha `get_document_content()`; adapter novo
  `infrastructure/startups_adapters/startups_adapter.py`
  (`StartupsModulePort`) — unica peca de `orchestration` que conhece
  `startups`
- `UrlIngestionJobView`/`UrlIngestionJobResponse` expoem `startup_id`,
  `recommendation_count`, `briefing_id` para polling do frontend;
  `POST /url-ingestion/jobs` aceita `startup_id` opcional (modo "associar
  a startup existente" em vez de criar uma nova)
- Migration `4c8a1f6e9b2d`: 4 colunas novas em `url_ingestion_jobs`
- Testes: +16 (7 unit em `test_url_ingestion_job.py`, 6 unit em
  `startups` para os 4 contratos novos, 1 integracao nova)

Documento da entrega: `docs/orchestration/orchestration_v2_jornada_completa.md`.

---

## Database state

### Migrations aplicadas

| Revisao | Data | Descricao |
|---|---|---|
| `f3f7f3959ccc` | 2026-06-13 | Cria tabelas scraping (jobs, attempts, results) |
| `a41c96d32e57` | 2026-06-15 | Torna content_hash unico em scraping_results |
| `d8e4a9c1b672` | 2026-06-15 | Adiciona campos de auditoria de agente em attempts |
| `7c9f2a1b4d6e` | 2026-06-15 | Cria tabelas de agents (agent_runs, agent_steps) |
| `9e1f3b5c8a2d` | 2026-06-16 | Cria tabelas de checkpoint LangGraph (V6) |
| `3f8d1e2a9c7b` | 2026-06-16 | Cria tabelas de ingestion (ingestion_jobs, documents, chunks) |
| `b7e2c4f8a1d3` | 2026-06-21 | Cria tabelas de embeddings (embedding_jobs, embedding_job_chunks) |
| `c19a4e5f6b20` | 2026-06-21 | Cria tabelas de startups (startups, startup_evidences) |
| `f90193dc1578` | 2026-06-21 | Cria tabela de recommendations |
| `782e2cbdbfab` | 2026-06-21 | Cria tabela de briefings |
| `2e85accbd38f` | 2026-06-21 | Cria tabela de analysis_jobs |
| `3ca1a725713e` | 2026-06-22 | Adiciona campos de classificacao de IA em startups |
| `8d84cba84a02` | 2026-06-22 | Cria indice GIN de full-text search em chunks (RAG V3) |
| `f77998c46d08` | 2026-06-22 | Adiciona campos estruturados em startups (founders/funding/customers) |
| `1d3e7f9a2b4c` | 2026-06-22 | Adiciona `source_type` em documents para separar startup_evidence/nvidia_knowledge |
| `2a7c9b8d1e5f` | 2026-06-22 | Adiciona `source_type` em ingestion_jobs para preservar contexto ate o worker |
| `5b6c7d8e9f01` | 2026-06-22 | Cria `url_ingestion_jobs` para Orchestration V2 |
| `7d4f2a9c6e83` | 2026-06-22 | Adiciona `source_type` em scraping_jobs para preservar origem desde a coleta |
| `4c8a1f6e9b2d` | 2026-06-23 | Adiciona `startup_id`/`evidence_attached`/`recommendation_count`/`briefing_id` em url_ingestion_jobs (Orchestration V2 jornada completa) |

**Head atual: `4c8a1f6e9b2d`**

### Tabelas existentes

```
scraping_jobs           status do job de scraping
scraping_attempts       cada tentativa de coleta com scores e decisao
scraping_results        conteudo bruto aprovado, pronto para ingestion
agent_runs              execucoes de agentes com input/output/status/agent_type
agent_steps             etapas auditaveis dentro de cada agent_run
checkpoints             estado LangGraph por thread_id (= agent_run.id)
checkpoint_blobs        conteudo de cada canal por versao
checkpoint_writes       escritas pendentes ate proximo checkpoint
checkpoint_migrations   versao das migrations internas do LangGraph
ingestion_jobs          status do job de ingestion (1-para-1 com scraping_result, source_type)
documents               documento limpo e normalizado (clean_text + word_count + chunk_count + source_type)
chunks                  fragmentos de texto prontos para embedding
embedding_jobs          status agregado do job de embeddings (1-para-1 com document)
embedding_job_chunks    status por chunk dentro de um embedding_job (attempt_count, error_message)
startups                empresa identificada (nome, setor, descricao, website, classificacao de maturidade de IA, founders, funding, customers)
startup_evidences       evidencia aprovada associada a uma startup (FK scraping_results)
recommendations         tecnologia NVIDIA recomendada por startup (score, justificativa, matched_keywords, evidence_ids)
briefings               briefing executivo em Markdown por startup (substitui o anterior a cada geracao)
analysis_jobs           historico de execucoes recommendations->briefing por startup (status, recommendation_count, briefing_id, error_message)
url_ingestion_jobs      orquestracao URL -> scraping -> ingestion -> embeddings -> startup -> recommendations -> briefing, com source_type/startup_id/recommendation_count/briefing_id
```

---

## Test coverage

| Modulo | Testes | Ultima verificacao |
|---|---|---|
| scraping | 134 | 2026-06-22 |
| agents | 99 unit + 1 integracao | 2026-06-23 |
| ingestion | 33 unit + 1 integracao | 2026-06-21 |
| embeddings | 56 unit + 2 integracao | 2026-06-21 |
| startups | 36 unit + 1 integracao | 2026-06-23 |
| rag | 17 unit + 1 integracao | 2026-06-22 |
| nvidia_knowledge | 15 unit | 2026-06-22 |
| recommendations | 24 unit + 1 integracao | 2026-06-23 |
| briefing | 15 unit + 1 integracao | 2026-06-21 |
| orchestration | 24 unit + 2 integracao | 2026-06-23 |
| shared | 10 unit (logging + observability, novo) | 2026-06-23 |
| **Total** | **474 passed, 2 warnings (Postgres/Redis/Qdrant ativos durante a verificacao)** | **2026-06-23** |

Nota: as linhas `ingestion`, `embeddings`, `rag`, `nvidia_knowledge`,
`briefing` nao foram reconferidas nesta verificacao — refletem a ultima
contagem conhecida, nao necessariamente o numero exato apos as entregas
mais recentes. `scraping`, `agents`, `startups`, `recommendations`,
`orchestration`, `shared` e o `Total` foram medidos de novo nesta entrega
(fix de matching/extraction em recommendations+startups+agents, logging
estruturado + Langfuse em shared, instrumentacao em orchestration).

Comando para verificar:
```bash
venv/Scripts/python.exe -m pytest apps/api/src/modules/ -q
```

---

## Current state summary (2026-06-21)

### Implemented and working
- **Scraping V8** — pipeline completa, worker operacional, 130 testes
- **Agents V7** — checkpoint PostgreSQL, human-in-the-loop completo (GET + POST /resume + interrupt() real), 57 unit testes
- **Ingestion V1** — TextCleaner, TextChunker, Document, Chunk, worker ingestion_worker, 33 unit + 1 integracao (contrato publico `IngestedDocumentReader` agora implementado)
- **Embeddings V4** — `EmbeddingService` (Gemini) + `VectorRepository` (Qdrant) + `EmbeddingJob`/`EmbeddingJobChunk` + worker em batch com retry/backoff, 56 unit + 2 integracao

### Historical next step note

The block below was written before Startups V1 and Embeddings V5 were finished.
For the current source of truth, use the "Authoritative Current State" section
at the top of this file and `docs/proximos_passos_mvp.md`.

### Previous next step (historical)
- **Embeddings V5** — reembedding e metricas (custo, latencia, modelo usado)
- **Startups V1** — modelo relacional de startups e evidencias, item 1 do backlog macro (`docs/roadmap_proximos_passos.md`)

### Backlog (in order)
1. Startups V1 — modelo relacional de startups
2. Embeddings V5 — reembedding e metricas
3. RAG V2 — busca semantica + resposta com citacoes
4. NVIDIA knowledge ingestion — base de conhecimento NVIDIA no Qdrant
5. Recommendations V1 — motor de recomendacao
6. Briefing V1 — relatorio executivo final

---

## Scraping module — key details

### Pipeline steps
1. **Strategy selection** — `ScrapingStrategySelector` picks ordered scrapers: BS4 (static HTML) → Playwright (JS-heavy) → Trafilatura (articles) → Firecrawl (paid fallback).
2. **Deterministic validation** — technical (HTTP status, captcha, timeout) + textual (word count, boilerplate ratio, text density) + basic evidential signals. All done by code, no LLM.
3. **Quality scoring** — `quality_score = technical_score × 0.30 + text_score × 0.30 + evidence_score × 0.40`
4. **Decision policy**:
   - `≥ 0.75` and no blockers → `ACCEPT`
   - `0.45 – 0.75` → `LLM_REVIEW` (light semantic validation by Gemini)
   - LLM `semantic_confidence < 0.80` or contradiction detected → `AGENT_REVIEW`
   - `< 0.45` with alternative strategy available → `FALLBACK`
   - `< 0.45` with no alternatives → `REJECT`
5. **Semantic validation (LLM)** — returns per-factor scores: `startup_match_score`, `evidence_clarity_score`, `source_reliability_score`, `statement_specificity_score`, `context_completeness_score`. System computes `semantic_confidence` from these factors — the LLM does NOT return a single confidence number.
6. **Agent investigation** — only when LLM is insufficient. Calls `modules/agents` via `SemanticInvestigator` port (public contract), never directly to graphs or LangGraph.

Every attempt is persisted to `scraping_attempts` table for debugging and metrics.

### Evidence strength levels
```
none   → no relevant evidence
weak   → mentions AI generically ("we use AI to transform businesses")
medium → describes an AI application in the product/operation
strong → describes application + technology + client/metric/real case
```

---

## Agents module — key details

### Architecture rules for agents
- **LangGraph orchestrates. LangChain integrates models and tools. Specialized modules execute.**
- Agent nodes must be small and testable — one responsibility per node.
- Routers must be deterministic when possible; LLM may suggest an action but a domain policy validates whether it is allowed.
- Never allow an open loop controlled only by the LLM — every graph must define `max_iterations`, `max_tool_calls`, `max_total_tokens`, `timeout_total`.
- LangGraph state must be serializable — no HTTP clients, SQLAlchemy sessions, or API keys in state.
- Tools are thin adapters: validate input → call a module's public contract → return small structured output.

### Graph state (what belongs in state)
```
run_id, target info, input text, semantic assessment results,
evidence items, search queries, sources consulted, contradictions,
iteration count, final decision, final reason
```

### What does NOT belong in state
```
HTTP clients, DB sessions, API keys, tool implementations,
non-serializable objects
```

### Agents planned (ordered by implementation priority)
1. Evidence Validation Agent — investigates semantically uncertain evidence
2. Search Planner Agent — transforms objective into queries and prioritized sources
3. Extraction Agent — structured extraction when simple rules are insufficient
4. Startup Classifier Agent — classifies AI-native / AI-enabled / Non-AI with evidence
5. NVIDIA RAG Agent — queries NVIDIA knowledge base with citations
6. Recommendation Agent — crosses tech gaps × NVIDIA catalog
7. Briefing Agent — organizes final output for the startup manager

### Human-in-the-loop (when to interrupt)
- Reliable sources contradict each other
- Startup identity remains uncertain after investigation
- Action has high cost
- Agent requests a broad new collection
- Decision may affect executive briefing
- Iteration limit reached

---

## Inter-module communication rules

### Allowed patterns
```
Module A → Module B's application/public/ contract
API/Module → Redis queue (job_id or run_id only) → Worker → Module factory/use case
```

### Forbidden patterns
```
Module A → Module B's domain/ entities (directly)
Module A → Module B's infrastructure/ models or repositories
Module A → Module B's graphs/ or nodes/
Worker → business logic (scraping, nodes, prompts, validation rules)
Queue message → full document or large payload
```

### Current inter-module calls
- `scraping` → `agents/application/public/semantic_investigator.py` (via adapter in `scraping/infrastructure/agent_adapters/`)
- `nvidia_knowledge` → `scraping/application/public/job_submitter.py` (via adapter in `nvidia_knowledge/infrastructure/scraping_adapters/`)
- `orchestration` → `startups/application/public/{startup_creator,evidence_attacher,extraction_trigger,classification_trigger}.py` (via adapter in `orchestration/infrastructure/startups_adapters/`)
- Both modules use `shared/queue/dramatiq_broker.py`

---

## Startup classification

After ingestion, startups are classified as:
- **AI-native** — AI is core to the product/operation (models are central, agents orchestrate workflows, proprietary data trains the system)
- **AI-enabled** — AI is a secondary feature (simple chatbot, summary feature, one small AI component)
- **Non-AI** — no strong AI evidence

This classification drives the recommendation engine and determines which NVIDIA technologies to recommend.

---

## NVIDIA technology mapping (recommendation rules)
```
LLMs in customer service          → NIM, NeMo Guardrails, Triton, TensorRT-LLM
High-volume tabular data          → RAPIDS, cuDF, cuML
Voice / speech processing         → NVIDIA Riva
Healthcare domain                 → Clara, MONAI, NIM, AI Enterprise
Robotics / simulation             → Isaac, Omniverse
Inference latency problems        → TensorRT-LLM, Triton Inference Server
Model serving at scale            → NVIDIA NIM, Triton
Generative AI fine-tuning         → NeMo
```

---

## Job status lifecycle

All async jobs follow: `pending → running → completed | failed`.
Optional intermediate states: `cancelled`, `retrying`, `partial`, `blocked`, `waiting_human_review`.

Status transitions are enforced by the domain entity, not by the worker or API layer. The frontend only polls via API; it never talks to workers or queues directly.

---

## Development commands

```bash
# Activate virtualenv (WSL / Git Bash)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run API (dev)
uvicorn apps.api.src.main:app --reload --port 8000

# Run a worker
python workers/scraper_worker/run.py
python workers/agent_worker/run.py

# Run all module tests
pytest apps/api/src/modules/ -q

# Run a specific module
pytest apps/api/src/modules/agents/tests/ -q

# Run a single test file
pytest apps/api/src/modules/scraping/tests/unit/test_policies.py -v

# Run by name
pytest -k "test_acceptance_policy_rejects_captcha" -v

# Run DB migrations
alembic upgrade head

# Current migration head: 4c8a1f6e9b2d (url_ingestion_jobs analysis fields)
```

---

## Environment variables

All env-var loading belongs in `apps/api/src/config/settings.py`. Never spread env-var access across modules.

```
DATABASE_URL
QDRANT_URL
QDRANT_COLLECTION_NAME   ← colecao de vetores de chunks (embeddings V3)
REDIS_URL
FIRECRAWL_API_KEY
LLM_API_KEY          ← Gemini API key
GEMINI_EMBEDDING_MODEL   ← modelo de embedding (embeddings V2), default models/text-embedding-004
COHERE_API_KEY       ← reranking RAG V4 (Cohere Rerank); opcional, sem ela busca segue sem reranking
LANGFUSE_PUBLIC_KEY  ← tracing de LLM (shared/observability); opcional, sem ela chamadas seguem sem tracing
LANGFUSE_SECRET_KEY
LANGFUSE_HOST        ← URL do Langfuse self-hosted, default http://localhost:3300 (infra/docker-compose.yml)
ENVIRONMENT
LOG_LEVEL
```

Variaveis do stack Langfuse self-hosted (infra/.env, nao a raiz - project
directory do `docker compose -f infra/docker-compose.yml` e' `infra/`):
ver `infra/.env.example`.

---

## Logging and observability

All logs must include relevant correlation IDs from: `request_id`, `job_id`, `startup_id`, `document_id`, `agent_run_id`. Track LLM call counts and costs per job — they are a significant operational expense. Never log API keys, tokens, or full sensitive documents.

---

## Security rules

- SSRF protection: block requests to `localhost`, `127.0.0.1`, `0.0.0.0`, RFC-1918 ranges, cloud metadata endpoints, and non-HTTP(S) schemes. Validate redirects.
- Secrets only in env vars or secret manager — never hardcoded.
- Web-scraped content is untrusted data — never treated as system instructions (prompt injection risk).
- Tools must validate inputs before calling external services.
- Never expose stack traces, credentials, or internal implementation details to the frontend.
- Agent actions with high cost or destructive side effects require a domain policy check.

---

## Docs reference (read before touching a module)

| Area | Document |
|---|---|
| Global architecture | `docs/arquitetura_global_monolito_modular_workers.md` |
| Current state | `docs/estado_atual_do_projeto.md` |
| Architectural validation | `docs/validacao_arquitetural_modulos_workers.md` |
| Module message contracts | `docs/validacao_mensagens_interacoes_modulos.md` |
| Roadmap | `docs/roadmap_proximos_passos.md` |
| MVP next steps | `docs/proximos_passos_mvp.md` |
| Scraping module | `docs/scraping/modulo_scraping_atualizado.md` |
| Scraping latest version | `docs/scraping/scraper_v8_agente_investigacao.md` |
| Agents module architecture | `docs/agents/modulo_agents_arquitetura.md` |
| Agents roadmap | `docs/agents/roadmap_agentes.md` |
| Agents V5 | `docs/agents/agents_v5_executar_grafos_pelo_agent_run.md` |
| Agents V6 | `docs/agents/agents_v6_checkpoint_postgres.md` |
| Agents V7 | `docs/agents/agents_v7_human_in_the_loop.md` |
| Agents V8 | `docs/agents/agents_v8_extraction_agent.md` |
| Agents V9 | `docs/agents/agents_v9_startup_classifier.md` |
| Agents V10 | `docs/agents/agents_v10_nvidia_rag_agent.md` |
| Agents V11 | `docs/agents/agents_v11_recommendation_agent.md` |
| Agents V12 (current) | `docs/agents/agents_v12_briefing_agent.md` |
| Embeddings V1 | `docs/embeddings/embeddings_v1_contratos_e_fake.md` |
| Embeddings V2+V3 | `docs/embeddings/embeddings_v2_v3_provider_real_e_qdrant.md` |
| Embeddings V4 | `docs/embeddings/embeddings_v4_worker_em_lote.md` |
| Embeddings V5 (current) | `docs/embeddings/embeddings_v5_metricas_reembedding.md` |
| RAG V3 (current) | `docs/rag/rag_v3_busca_hibrida.md` |
| RAG V4 (current) | `docs/rag/rag_v4_reranking.md` |
| RAG roadmap | `docs/rag/roadmap_rag.md` |
| Startups V2 (current) | `docs/startups/startups_v2_campos_estruturados.md` |
| Startups V3 (current) | `docs/startups/startups_v3_classificacao_maturidade.md` |
| Startups roadmap | `docs/startups/roadmap_startups.md` |
| NVIDIA Knowledge roadmap | `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` |
| NVIDIA Knowledge V2 foundation | `docs/nvidia_knowledge/nvidia_knowledge_v2_foundation_source_type.md` |
| NVIDIA Knowledge V2 source registry | `docs/nvidia_knowledge/nvidia_knowledge_v2_source_registry.md` |
| NVIDIA Knowledge V2 primeira validacao real (current) | `docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md` |
| Recommendations V1 (current) | `docs/recommendations/recommendations_v1_regras_deterministicas.md` |
| Recommendations roadmap | `docs/recommendations/roadmap_recommendations.md` |
| Briefing V1 (current) | `docs/briefing/briefing_v1_template_executivo.md` |
| Briefing roadmap | `docs/briefing/roadmap_briefing.md` |
| Orchestration V1 (current) | `docs/orchestration/orchestration_v1_analysis_jobs.md` |
| Orchestration V2 URL ingestion jobs | `docs/orchestration/orchestration_v2_url_ingestion_jobs.md` |
| Orchestration V2 worker automatico | `docs/orchestration/orchestration_v2_worker_automatico.md` |
| Orchestration V2 jornada completa (current) | `docs/orchestration/orchestration_v2_jornada_completa.md` |
| Orchestration roadmap | `docs/orchestration/roadmap_orchestration.md` |
| Diagnostico vs. case original + prioridades | `docs/diagnostico_case_original_e_novas_prioridades.md` |
| Estado atual do projeto | `docs/estado_atual_do_projeto.md` |
