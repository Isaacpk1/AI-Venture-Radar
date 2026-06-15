# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Conversation style

End every response to the user with: **bora bill**

## Project overview

**NVIDIA Startup AI Radar** — a pipeline that collects public data about AI startups, processes it, and generates structured NVIDIA technology recommendations with justifications. The output is an executive briefing per startup.

The system is purpose-built to identify whether a startup is AI-native, AI-enabled, or Non-AI, then match it to the right NVIDIA technologies (NIM, TensorRT-LLM, Triton, RAPIDS, Riva, MONAI, etc.).

## Tech stack

| Layer | Technology |
|---|---|
| API | Python 3.13 + FastAPI |
| Frontend | Next.js + TypeScript + Tailwind + TanStack Query |
| Relational DB | PostgreSQL (or Supabase) |
| Vector DB | Qdrant |
| Queue | Redis + Dramatiq |
| Scraping | BeautifulSoup, Playwright, Trafilatura, Firecrawl |
| LLM orchestration | LangGraph |
| Reranking | Cohere Rerank or cross-encoder |
| Virtual env | `venv/` at repo root (Python 3.13) |

## Repository layout

```
apps/
  api/src/
    main.py             ← FastAPI entrypoint
    modules/            ← business modules (scraping, ingestion, startups, rag, agents, recommendations)
    database/           ← relational/ and vector/ clients
    shared/             ← logger, errors, auth, observability
    config/             ← all env-var loading (DATABASE_URL, QDRANT_URL, REDIS_URL, FIRECRAWL_API_KEY, etc.)
  web/src/              ← Next.js frontend
workers/                ← separate processes; each calls a module use case
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

## Module internal structure

Every module under `apps/api/src/modules/<name>/` follows the same layered pattern:

```
presentation/   ← FastAPI routes, schemas (requests/responses), exception handlers
application/    ← use cases, pipelines, services, ports (interfaces), DTOs
domain/         ← entities, value objects, enums, repository contracts, policies, exceptions
infrastructure/ ← database models/mappers/repositories, scrapers, clients, validators, queue adapters
factories/      ← wires everything together (only place that knows all concrete types)
tests/          ← unit/, integration/, fixtures/
```

**Dependency rules** (strictly enforced):
- `presentation → application → domain` (one direction only)
- `infrastructure → domain` and `infrastructure → application` (implements ports)
- `factories` connect all layers
- `domain` must never import from infrastructure, FastAPI, or SQLAlchemy
- `application` must never import from Playwright, BeautifulSoup, SQLAlchemy, etc.
- Workers live outside modules; they import only from `factories/` or public `application/` contracts

## Development commands

```bash
# Activate virtualenv (Windows/WSL)
source venv/Scripts/activate     # Git Bash / WSL
# or
venv\Scripts\activate            # PowerShell

# Install dependencies (once requirements files exist)
pip install -r requirements.txt

# Run API (dev)
uvicorn apps.api.src.main:app --reload --port 8000

# Run a worker
python workers/scraper_worker/run.py

# Run tests
pytest apps/api/src/modules/<module>/tests/

# Run a single test file
pytest apps/api/src/modules/scraping/tests/unit/test_policies.py -v

# Run a single test by name
pytest -k "test_acceptance_policy_rejects_captcha" -v
```

## Key architectural rules

**Workers never contain business logic.** They receive a `job_id` from the queue and call the module's use case:

```python
# workers/scraper_worker/tasks.py
from apps.api.src.modules.scraping.factories.scraping_factory import ScrapingFactory

async def execute_scraping_job(job_id: str) -> None:
    use_case = ScrapingFactory.create_execute_scraping_job()
    await use_case.execute(UUID(job_id))
```

**Queue messages carry only IDs**, never full documents. The worker fetches data from the database using the ID.

**Inter-module communication uses public contracts only.** A module exposes a public reader/service in `application/public/`. Other modules import that contract, never internal models or DB tables.

**PostgreSQL is the source of truth.** Qdrant stores vectors for semantic search, but every vector must reference a real chunk/document ID in PostgreSQL.

## Scraping module — key details

This is the first module being built. Its pipeline (`ScrapingPipeline`) runs:

1. **Strategy selection** — `ScrapingStrategySelector` picks ordered scrapers based on URL/source type (order varies: BS4 for static HTML, Playwright for JS-heavy, Trafilatura for articles, Firecrawl as paid fallback)
2. **Deterministic validation** — technical (HTTP status, captcha, timeouts) + textual (word count, boilerplate ratio, text density) + basic evidential signals
3. **Quality scoring** — `quality_score = technical_score*0.30 + text_score*0.30 + evidence_score*0.40`
4. **Decision policy**:
   - `>= 0.75` and no blockers → `ACCEPT`
   - `0.45–0.75` → `LLM_REVIEW` (light semantic validation)
   - LLM confidence `< 0.80` or contradiction detected → `AGENT_REVIEW`
   - `< 0.45` with alternative strategy → `FALLBACK` (try next scraper)
   - `< 0.45` with no alternatives → `REJECT`
5. **Semantic validation (LLM)** — returns per-factor scores (`startup_match_score`, `evidence_clarity_score`, `source_reliability_score`, `statement_specificity_score`, `context_completeness_score`) and a `decision` enum. The system calculates `semantic_confidence` from these factors, not from a single LLM-provided number.
6. **Agent investigation** — only when LLM is insufficient; calls `modules/agents` via the `SemanticInvestigator` port

Every attempt is persisted to `scraping_attempts` table for debugging and metrics.

## Startup classification

After ingestion, startups are classified as:
- **AI-native** — AI is core to the product/operation
- **AI-enabled** — AI is a secondary feature
- **Non-AI** — no strong AI evidence

This classification drives the recommendation engine.

## Job status lifecycle

All async jobs follow: `pending → running → completed | failed`. Optional: `cancelled`, `retrying`, `partial`. Status transitions must be enforced by the domain entity. The frontend only polls via API; it never talks to workers or queues directly.

## Environment variables

All env-var loading belongs in `apps/api/src/config/`. Variables expected:

```
DATABASE_URL
QDRANT_URL
REDIS_URL
FIRECRAWL_API_KEY
LLM_API_KEY
COHERE_API_KEY
ENVIRONMENT
LOG_LEVEL
```

## Logging and observability

All logs must include correlation IDs: `request_id`, `job_id`, `startup_id`, `document_id`, `agent_run_id`. Track LLM call counts and costs per job — they're a significant operational expense.

## SSRF protection

The scraping infrastructure must block requests to `localhost`, `127.0.0.1`, `0.0.0.0`, RFC-1918 ranges, cloud metadata endpoints, and non-HTTP(S) schemes. Validate redirects too.
