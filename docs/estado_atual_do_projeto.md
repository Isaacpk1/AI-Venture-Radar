# Estado Atual do Projeto - NVIDIA Startup AI Radar

Documento de referencia do estado real em 26/06/2026. Para o detalhe completo de cada entrega, ver `CLAUDE.md` secao "Authoritative Current State" e os roadmaps por modulo.

---

## Resumo

O MVP esta implementado de ponta a ponta:

```txt
URL -> scraping -> ingestion -> embeddings -> startups -> rag
-> recommendations -> briefing -> frontend
```

Tambem existem os 8 agentes do brief original em LangGraph: Evidence Validation, Search Planner, Extraction, Startup Classifier, NVIDIA RAG, Recommendation e Briefing, alem da infraestrutura generica de `agent_runs`.

O frontend Next.js cobre a jornada URL -> job -> resultado da startup, portfolio paginado, historico global de jobs, chatbot NVIDIA Knowledge, badge de fit, evidencia clicavel por recomendacao, export PDF, dashboard de portfolio, comparacao de startups, fila em lote e revisao humana simples de recommendations/briefings. Startup Discovery V1 tambem esta entregue para descobrir URLs em hubs publicos e alimentar `url_ingestion_jobs`.

---

## Modulos Implementados

| Modulo | Versao atual | Observacao |
|---|---|---|
| scraping | V8 | Pipeline com validacao deterministica, Gemini e agent review |
| agents | V12 | 8/8 agentes do brief, com Recommendation/Briefing ligados ao caminho sincrono |
| ingestion | V1 | `documents`/`chunks` + worker |
| embeddings | V5 | Metricas por job/chunk, cache por `content_hash`, guarda de schema do Qdrant e limpeza de vetores orfaos |
| startups | V4 | Dados estruturados, classificacao AI-native/AI-enabled/Non-AI, listagem paginada, stats e dedup por nome/dominio |
| rag | V4 | Busca vetorial + BM25 via `pg_search`, RRF, reranking Cohere e resposta citada |
| nvidia_knowledge | V1 + V2 | Catalogo + registry; 20/20 fontes processadas, 17/20 com conteudo recuperavel |
| recommendations | V3 | Regras deterministicas + RAG grounding + `confidence`/`complexity` + stats de tecnologias |
| briefing | V3 | Markdown executivo, contexto NVIDIA via RAG e export PDF via Playwright/Jinja2 |
| orchestration | V1 + V2.1 | `analysis_jobs` e `url_ingestion_jobs` ponta a ponta, com worker automatico e primeira rodada de enriquecimento por dominio |
| startup_discovery | V1 | InovAtiva Brasil, Abstartups e 100 Open Startups; persiste runs e submete URLs descobertas |
| frontend | V5 | Jornada operacional, portfolio, historico, chat, PDF, dashboard, comparacao, lote e revisao humana simples |

---

## Rotas Expostas

```txt
/health
/scraping/jobs
/scraping/results/{result_id}
/agents/runs/{run_id}
/agents/runs/{run_id}/resume
/ingestion/jobs
/embeddings/jobs
/startups
/startups/stats
/startups/{startup_id}
/startups/{startup_id}/evidences
/startups/{startup_id}/extract
/startups/{startup_id}/classify
/rag/search
/rag/answer
/nvidia-knowledge/technologies
/nvidia-knowledge/sources
/nvidia-knowledge/ingestion/jobs
/recommendations
/recommendations/stats
/briefings
/briefings/{briefing_id}/export
/briefings/{briefing_id}/review
/analysis/jobs
/url-ingestion/jobs
/startup-discovery/runs
/startup-discovery/runs/{run_id}
```

---

## Banco e Migrations

Head atual: `f4b2a9c8d6e1`.

```txt
f3f7f3959ccc  scraping tables
a41c96d32e57  content_hash unico em scraping_results
d8e4a9c1b672  campos de auditoria de agent em attempts
7c9f2a1b4d6e  agent_runs e agent_steps
9e1f3b5c8a2d  checkpoint LangGraph
3f8d1e2a9c7b  ingestion tables
b7e2c4f8a1d3  embedding tables
c19a4e5f6b20  startup tables
f90193dc1578  recommendations
782e2cbdbfab  briefings
2e85accbd38f  analysis_jobs
3ca1a725713e  classificacao em startups
8d84cba84a02  indice FTS de chunks (substituido por BM25)
f77998c46d08  campos estruturados em startups
1d3e7f9a2b4c  source_type em documents
2a7c9b8d1e5f  source_type em ingestion_jobs
5b6c7d8e9f01  url_ingestion_jobs
7d4f2a9c6e83  source_type em scraping_jobs
4c8a1f6e9b2d  jornada completa em url_ingestion_jobs
b3f6e91c7d45  BM25 (`pg_search`) em chunks
c9d3e7f0a4b8  startup_discovery_runs
e8a7c4d2b1f9  review_status/review_comment/reviewed_by/reviewed_at em recommendations e briefings
f4b2a9c8d6e1  parent_job_id/enrichment_round em url_ingestion_jobs
```

Tabelas principais:

```txt
scraping_jobs, scraping_attempts, scraping_results
agent_runs, agent_steps, checkpoints/*
ingestion_jobs, documents, chunks
embedding_jobs, embedding_job_chunks
startups, startup_evidences
recommendations
briefings
analysis_jobs
url_ingestion_jobs
startup_discovery_runs
```

---

## Testes

Ultima validacao completa registrada com infra local ativa:

```txt
Backend: 559 passed, 1 skipped
Frontend: 25 passed
```

O codigo atual ja inclui testes adicionais de Frontend V5 e `startup_discovery`; `CLAUDE.md` registra 568 testes backend coletados e 30 testes frontend coletados em 25/06/2026. O teste Ragas continua opt-in via `RUN_RAGAS_EVAL=1`.

---

## O Que Falta

Para o MVP/demo macro, nada estrutural grande. O que permanece:

```txt
Frontend V5: revisao humana simples entregue, sem auth completa - ENTREGUE.
Chain de enriquecimento quando a fonte inicial e fraca: jobs filhos do mesmo dominio e executor Tavily opcional entregues; falta validar com chave real e calibrar ranking/allowlist.
Expandir Startup Discovery para mais hubs gratuitos alem dos 3 iniciais.
Auth, CI/CD, deploy e backup do Qdrant: fora de escopo deliberadamente.
```

---

## Proximo Passo Recomendado

```txt
Validar a chain de enriquecimento com Tavily real e calibrar ranking/allowlist das fontes externas.
```
