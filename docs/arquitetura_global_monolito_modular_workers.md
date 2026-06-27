# Arquitetura Global - Monolito Modular + Workers

Atualizado em 26/06/2026.

---

## Visao Geral

```txt
FastAPI
  -> modulos sincronicos
  -> jobs em PostgreSQL
  -> workers Dramatiq para tarefas longas
  -> Qdrant para busca vetorial
  -> LangGraph para agentes
  -> Next.js como frontend/BFF
```

O backend e um monolito modular. Cada modulo tem fronteiras proprias, contratos
publicos em `application/public/` quando precisa conversar com outro modulo, e
implementacoes concretas isoladas em `infrastructure/`.

---

## Modulos

```txt
scraping            coleta e valida evidencias publicas
agents              grafos LangGraph e agent_runs
ingestion           documents/chunks a partir de scraping_results
embeddings          embeddings e Qdrant
startups            perfil relacional, evidencias, extracao, classificacao e stats
rag                 busca hibrida, reranking e resposta citada
nvidia_knowledge    catalogo NVIDIA e registry de fontes oficiais
recommendations     recomendacoes NVIDIA rastreaveis, confidence/complexity e stats
briefing            briefing executivo em Markdown e PDF
orchestration       analysis_jobs e url_ingestion_jobs ponta a ponta
startup_discovery   descobre URLs em hubs publicos e alimenta url_ingestion_jobs
frontend            Next.js App Router, BFF `/api/radar`, telas operacionais
```

---

## Workers

```txt
workers/scraper_worker       fila scraping       job_id
workers/agent_worker         fila agents         run_id
workers/ingestion_worker     fila ingestion      job_id
workers/embedding_worker     fila embeddings     job_id
workers/orchestration_worker fila url_ingestion  job_id
```

Workers nao contem regra de negocio; apenas recebem IDs e chamam factories/use
cases.

---

## Fluxos

### URL Ate Briefing

```txt
POST /url-ingestion/jobs
-> orchestration_worker
-> scraping
-> ingestion
-> embeddings/Qdrant
-> criar ou associar startup
-> anexar evidencia
-> extract/classify
-> recommendations
-> briefing
```

### Descoberta De Startups

```txt
POST /startup-discovery/runs
-> extratores de hubs publicos
-> URLs descobertas
-> url_ingestion_jobs
GET /startup-discovery/runs/{id}
```

Startup Discovery V1 cobre tres hubs iniciais: InovAtiva Brasil, Abstartups e
100 Open Startups. A expansao para os demais hubs gratuitos e evolucao futura.

### Perfil, Portfolio E Dashboard

```txt
POST /startups
GET  /startups?page=1&page_size=20
GET  /startups/stats
GET  /startups/{id}
PATCH /startups/{id}
POST /startups/{id}/evidences
POST /startups/{id}/extract
POST /startups/{id}/classify
```

### RAG, Recomendacao E Briefing

```txt
POST /rag/search
POST /rag/answer
GET  /nvidia-knowledge/technologies
GET  /nvidia-knowledge/sources
POST /nvidia-knowledge/ingestion/jobs
POST /recommendations
GET  /recommendations/stats
POST /briefings
GET  /briefings/{id}/export
POST /analysis/jobs
```

---

## Estado Atual

O MVP backend e frontend por URL estao funcionais:

```txt
URL -> scraping -> ingestion -> embeddings -> startup/extract/classify
-> recommendations -> briefing -> frontend
```

Tambem estao entregues portfolio paginado, historico global de jobs,
dashboard de portfolio, comparacao de startups, fila em lote, chatbot NVIDIA
Knowledge, export PDF e Startup Discovery V1.

---

## Proximas Decisoes Arquiteturais

```txt
1. Como executar a chain de enriquecimento quando uma primeira URL for fraca.
2. Como expandir Startup Discovery para mais hubs sem virar crawler caro.
3. Como instrumentar metricas/alertas de producao se o demo virar produto.
4. Como implementar revisao humana simples sem auth completa.
```
