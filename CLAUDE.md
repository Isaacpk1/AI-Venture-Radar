# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
    shared/             ← logger, errors, auth, observability, queue/dramatiq_broker.py
    config/             ← all env-var loading
  web/src/              ← Next.js frontend
workers/                ← separate processes; thin delegators only
  scraper_worker/       ← run.py + tasks.py
  ingestion_worker/
  embedding_worker/
  agent_worker/
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

## Current implementation state (as of 2026-06-15)

### What is fully implemented
- **Scraping module** — complete: domain, application, infrastructure, factories, presentation, tests. Pipeline: BS4 → Playwright → Trafilatura → Firecrawl fallback. Full deterministic + semantic validation. PostgreSQL persistence. Worker (`scraper_worker`) operational.
- **Agents module — V5** — worker executes the correct graph by `agent_type`. `ExecuteAgentJob` receives `EvidenceValidationService` and `SearchPlanningService` via factory. Real output saved to `agent_runs.output_payload`. Real `AgentStep` saved with name `execute_{agent_type}`. LLM failures → `run.fail(reason)`. `AgentServiceUnavailableError` when API key is absent. 167 tests passing.

### What is pending (next steps in order)
1. **Agents V6** — LangGraph checkpoint in PostgreSQL (resume after failure, human-in-the-loop, graph state audit).
2. **Ingestion module** — clean, normalize, extract, chunk `scraping_results` into `documents` and `chunks`.
3. **Startups module** — structured relational model for startups and their evidences.
4. **Embeddings + Qdrant** — embed chunks, store in Qdrant with references to PostgreSQL chunk IDs.
5. **RAG module** — hybrid search (BM25/PG full-text + Qdrant semantic), reranking, context assembly, LLM answer with citations.
6. **NVIDIA knowledge ingestion** — ingest NVIDIA tech docs into Qdrant.
7. **Recommendations module** — cross startup profile × NVIDIA tech catalog → recommendations with justification.
8. **Briefing** — structured executive output per startup.

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

# Current migration head: 7c9f2a1b4d6e (agent_run tables)
```

---

## Environment variables

All env-var loading belongs in `apps/api/src/config/settings.py`. Never spread env-var access across modules.

```
DATABASE_URL
QDRANT_URL
REDIS_URL
FIRECRAWL_API_KEY
LLM_API_KEY          ← Gemini API key
COHERE_API_KEY
ENVIRONMENT
LOG_LEVEL
```

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
| Full pipeline logic | `docs/logica_do_sistema.md` |
| Architectural validation | `docs/validacao_arquitetural_modulos_workers.md` |
| Module message contracts | `docs/validacao_mensagens_interacoes_modulos.md` |
| Roadmap | `docs/roadmap_proximos_passos.md` |
| Scraping module | `docs/scraping/modulo_scraping_atualizado.md` |
| Scraping latest version | `docs/scraping/scraper_v8_agente_investigacao.md` |
| Agents module architecture | `docs/agents/modulo_agents_arquitetura.md` |
| Agents roadmap | `docs/agents/roadmap_agentes.md` |
| Agents V4 (current) | `docs/agents/agents_v4_agent_runs_persistence.md` |
