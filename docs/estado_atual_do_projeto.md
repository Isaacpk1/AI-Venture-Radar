# Estado Atual do Projeto — NVIDIA Startup AI Radar

Documento de referencia do estado real do sistema em 16/06/2026.

---

## 1. Visao Geral

O NVIDIA Startup AI Radar e uma pipeline que coleta dados publicos sobre startups,
valida a qualidade dessas evidencias, classifica o nivel de maturidade em IA e gera
recomendacoes personalizadas de tecnologias NVIDIA.

O sistema esta sendo construido em fases verticais: cada fase adiciona uma camada real
de funcionamento, do scraping ate o briefing executivo final.

---

## 2. O que esta funcionando hoje

### 2.1 Modulo de Scraping — Completo

O modulo de scraping e o mais maduro do projeto. Ele recebe uma URL, coleta o
conteudo, valida em tres niveis e decide se o conteudo serve como evidencia.

**Pipeline de execucao:**

```
URL de entrada
  -> estrategia de scraping (BeautifulSoup / Playwright / Trafilatura / Firecrawl)
  -> validacao tecnica (HTTP, captcha, timeout, HTML vazio)
  -> validacao textual (word count, boilerplate ratio, text density)
  -> validacao evidencial (sinais de IA, nome da startup, tipo de fonte)
  -> quality_score = technical * 0.30 + text * 0.30 + evidence * 0.40
  -> decisao: ACCEPT | LLM_REVIEW | AGENT_REVIEW | FALLBACK | REJECT
  -> [se LLM_REVIEW] -> Gemini avalia fatores semanticos
  -> [se AGENT_REVIEW] -> Evidence Validation Agent investiga
  -> resultado aceito salvo em scraping_results
```

**Camadas implementadas:**

```
domain/         entidades ScrapingJob, ScrapingAttempt, ScrapingResult
                politicas de decisao por quality_score
application/    pipeline de scraping, estrategia de selecao de scrapers
                casos de uso: CreateScrapingJob, ExecuteScrapingJob, GetScrapingResult
infrastructure/ scrapers: BeautifulSoup, Playwright, Trafilatura
                validadores deterministicos: tecnico, textual, evidencial
                validador semantico: Gemini (LangChain)
                adapter para o modulo agents (SemanticInvestigator)
                repositorios PostgreSQL com SQLAlchemy async
                fila via Redis + Dramatiq
factories/      ScrapingFactory conecta todas as camadas
presentation/   rotas FastAPI (CreateScrapingJob, GetScrapingJob, GetScrapingResult)
tests/          130 testes (unit + integration)
```

**Worker operacional:**

```
workers/scraper_worker/
  -> consome fila "scraping"
  -> recebe job_id
  -> chama ScrapingFactory.create_execute_scraping_job()
  -> nao contem regra de negocio
```

**Tabelas no PostgreSQL:**

```
scraping_jobs      status do job (pending -> running -> completed/failed)
scraping_attempts  cada tentativa de coleta com scores e decisao
scraping_results   conteudo bruto aprovado, pronto para ingestion
```

---

### 2.2 Modulo de Agents — V5 (Atual)

O modulo de agents orquestra fluxos que exigem multiplas etapas e decisoes
condicionais. Ele usa LangGraph para estruturar os grafos e LangChain para
integrar o Gemini.

**Evolucao do modulo:**

| Versao | O que foi entregue |
|---|---|
| V1 | Contrato publico `SemanticInvestigator` + Gemini simples |
| V2 | `EvidenceValidationGraph` com LangGraph real |
| V3 | `SearchPlanningGraph` (Search Planner Agent) |
| V3.5 | `agent_worker` base + dispatcher Dramatiq |
| V4 | `agent_runs` e `agent_steps` persistidos no PostgreSQL |
| V5 | Worker executa o grafo correto por `agent_type` ← **versao atual** |

**O que a V5 faz:**

```
agent_worker recebe run_id da fila "agents"
  -> busca AgentRun no PostgreSQL
  -> reconstroi o DTO de entrada via agent_run_payloads
  -> despacha para o grafo correto:
       EVIDENCE_VALIDATION -> EvidenceValidationGraph -> investigate()
       SEARCH_PLANNING     -> SearchPlanningGraph     -> plan_searches()
  -> salva output real em agent_runs.output_payload
  -> salva AgentStep real ("execute_evidence_validation" ou "execute_search_planning")
  -> falhas de LLM ou grafo -> run.fail(reason) -> status FAILED
```

**Grafos implementados:**

```
EvidenceValidationGraph
  nodes: prepare_context -> judge_evidence -> finalize
  entrada: EvidenceValidationInput (URL, texto, scores, resultado semantico anterior)
  saida:   EvidenceValidationResult (decision: accepted/rejected/needs_more_sources, reason)

SearchPlanningGraph
  nodes: prepare_context -> generate_plan -> finalize
  entrada: SearchPlanInput (startup_name, source_url, raw_text, reason)
  saida:   SearchPlanResult (queries com query/purpose/priority, reason)
```

**Contratos publicos expostos:**

```
application/public/semantic_investigator.py  <- EvidenceValidationService (ABC)
application/public/search_planner.py         <- SearchPlanningService (ABC)
```

**Camadas implementadas:**

```
domain/         AgentRun, AgentStep com transicoes de status controladas
                AgentType (evidence_validation, search_planning)
                AgentRunStatus (pending, running, completed, failed)
application/    CreateAgentRun, ExecuteAgentJob, GetAgentRun
                agent_run_payloads: serializa/deserializa DTOs <-> JSON do banco
infrastructure/ LangChainGeminiEvidenceJudge (adaptador LangChain/Gemini)
                LangChainGeminiSearchPlanner (adaptador LangChain/Gemini)
                PostgresAgentRunRepository, PostgresAgentStepRepository
                PostgresAgentsUnitOfWork
                DramatiqAgentDispatcher
graphs/         EvidenceValidationGraph, SearchPlanningGraph
factories/      AgentsFactory injeta servicos concretos no ExecuteAgentJob
tests/          37 testes (unit + integration)
```

**Worker operacional:**

```
workers/agent_worker/
  -> consome fila "agents"
  -> recebe run_id
  -> chama AgentsFactory.create_execute_agent_job()
  -> executa o grafo correto (V5)
```

**Tabelas no PostgreSQL:**

```
agent_runs    execucao de agente com input/output/status/agent_type
agent_steps   etapas auditaveis dentro de cada execucao
```

---

## 3. Infraestrutura compartilhada

**Broker Dramatiq:**

```
apps/api/src/shared/queue/dramatiq_broker.py
  -> RedisBroker configurado uma vez
  -> usado por scraping e agents
  -> usado por scraper_worker e agent_worker
```

**Banco de dados:**

```
PostgreSQL (async via SQLAlchemy 2.x)
  -> sessao via AsyncSessionFactory
  -> migracao via Alembic
```

**Config centralizada:**

```
apps/api/src/config/settings.py
  DATABASE_URL, REDIS_URL, GEMINI_API_KEY, GEMINI_MODEL,
  FIRECRAWL_API_KEY, COHERE_API_KEY, ENVIRONMENT, LOG_LEVEL
```

---

## 4. Migrations aplicadas

| Revisao | Data | Descricao |
|---|---|---|
| `f3f7f3959ccc` | 2026-06-13 | Cria tabelas de scraping (jobs, attempts, results) |
| `a41c96d32e57` | 2026-06-15 | Torna content_hash unico em scraping_results |
| `d8e4a9c1b672` | 2026-06-15 | Adiciona campos de auditoria de agente em attempts |
| `7c9f2a1b4d6e` | 2026-06-15 | Cria tabelas de agents (agent_runs, agent_steps) |

**Head atual:**

```
7c9f2a1b4d6e
```

---

## 5. Testes

| Modulo | Testes |
|---|---|
| scraping | 130 |
| agents | 37 |
| **Total** | **167** |

Todos os testes sao passados sem falhas.

Os testes unitarios usam fakes e in-memory repositories.
Os testes de integracao validam a camada PostgreSQL com banco real.

---

## 6. Arquitetura do fluxo atual

O que o sistema consegue fazer hoje de ponta a ponta:

```
1. API recebe URL via POST /scraping/jobs
2. Cria ScrapingJob (pending) no PostgreSQL
3. Publica job_id na fila "scraping"
4. scraper_worker consome job_id
5. Executa pipeline de scraping (BS4/Playwright/Trafilatura/Firecrawl)
6. Valida conteudo (tecnico + textual + evidencial)
7. Se quality_score ambiguo (0.45-0.75):
   -> Gemini faz revisao semantica
   -> Se semantic_confidence < 0.80:
      -> Cria AgentRun (pending) no PostgreSQL
      -> Publica run_id na fila "agents"
      -> agent_worker executa EvidenceValidationGraph
      -> Resultado salvo em agent_runs.output_payload
8. Conteudo aceito salvo em scraping_results
9. API retorna resultado via GET /scraping/results/{id}
```

O que ainda nao existe (proximas fases):

```
ingestion    -> limpar, normalizar, chunkar scraping_results
startups     -> modelo relacional de startups e evidencias
embeddings   -> vetorizar chunks com modelo de embedding
qdrant       -> busca semantica sobre os chunks
rag          -> busca hibrida + reranking + resposta com citacoes
recommendations -> cruzar perfil da startup com tecnologias NVIDIA
briefing     -> relatorio executivo final
```

---

## 7. Comunicacao entre modulos

```
scraping -> agents (chamada direta por contrato publico)
  scraping/infrastructure/agent_adapters/agents_semantic_investigator.py
  importa: agents/application/public/semantic_investigator.py
  nao importa: grafos, nodes, LangGraph, Gemini

API -> fila -> worker -> modulo (para operacoes longas)
  mensagem = {job_id} ou {run_id}  <- somente identificadores
  worker nao tem logica de negocio
  worker chama factory/use case do modulo

broker Redis/Dramatiq = infraestrutura compartilhada em shared/
```

---

## 8. O que esta pendente (proximos passos em ordem)

As proximas partes do sistema agora sao documentadas como modulos versionados
independentes. Ou seja, nao existe uma "V9 do projeto inteiro". Existe:

```txt
Scraping V8
Agents V5
Ingestion V1
Embeddings V1
RAG V1
Recommendations V1
Briefing V1
```

### Agents V6 — Checkpoint LangGraph
Permitir retomada de grafos apos falha, human-in-the-loop e auditoria de estado.

Entregaveis:
```
PostgresCheckpointer para LangGraph
estado do grafo salvo entre nodes
API para aprovar/rejeitar interrupcoes
status waiting_human_review
```

### Modulo Ingestion V1
Transformar `scraping_results` em `documents` e `chunks` limpos e prontos para embedding.

Entregaveis:
```
Contrato publico do scraping (ScrapingResultReader)
Entidades: IngestionJob, Document, Chunk
Servicos de dominio: TextCleaner, TextChunker
Caso de uso: ExecuteIngestionJob
Repositorios PostgreSQL
Migration: ingestion_jobs, documents, chunks
Worker: ingestion_worker
```

### Modulo Startups V1
Representacao estruturada das empresas analisadas.

### Embeddings + Qdrant
Vetorizacao dos chunks e busca semantica.

### RAG
Busca hibrida + reranking + resposta fundamentada com citacoes.

### Recommendations
Cruzamento de perfil da startup com catalogo NVIDIA.

### Briefing
Relatorio executivo final para o gerente de startups.

---

## 9. Referencia de documentos

| Documento | Caminho |
|---|---|
| Arquitetura global | `docs/arquitetura_global_monolito_modular_workers.md` |
| Logica do sistema | `docs/logica_do_sistema.md` |
| Validacao arquitetural | `docs/validacao_arquitetural_modulos_workers.md` |
| Mensagens entre modulos | `docs/validacao_mensagens_interacoes_modulos.md` |
| Roadmap geral | `docs/roadmap_proximos_passos.md` |
| Modulo scraping | `docs/scraping/modulo_scraping_atualizado.md` |
| Modulo agents | `docs/agents/modulo_agents_arquitetura.md` |
| Roadmap agents | `docs/agents/roadmap_agentes.md` |
| Agents V5 (atual) | `docs/agents/agents_v5_executar_grafos_pelo_agent_run.md` |
| Roadmap ingestion | `docs/ingestion/roadmap_ingestion.md` |
| Roadmap startups | `docs/startups/roadmap_startups.md` |
| Roadmap embeddings | `docs/embeddings/roadmap_embeddings.md` |
| Roadmap RAG | `docs/rag/roadmap_rag.md` |
| Roadmap NVIDIA Knowledge | `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` |
| Roadmap recommendations | `docs/recommendations/roadmap_recommendations.md` |
| Roadmap briefing | `docs/briefing/roadmap_briefing.md` |
