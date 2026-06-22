# Estado Atual do Projeto - NVIDIA Startup AI Radar

Documento de referencia do estado real em 22/06/2026.

---

## Resumo

O backend modular do MVP esta implementado de ponta a ponta:

```txt
scraping -> ingestion -> embeddings -> startups -> rag -> recommendations
-> briefing -> orchestration
```

Tambem existem agentes LangGraph para validacao de evidencia, planejamento de
busca, extracao estruturada e classificacao de maturidade em IA.

---

## Modulos Implementados

| Modulo | Versao atual | Observacao |
|---|---|---|
| scraping | V8 | pipeline com validacao deterministica, Gemini e agent review |
| agents | V9 | Evidence, Search Planner, Extraction e Startup Classifier |
| ingestion | V1 | documents/chunks + worker |
| embeddings | V5 | Gemini embeddings, Qdrant, worker, metricas |
| startups | V3 | dados estruturados + classificacao AI-native/AI-enabled/Non-AI |
| rag | V4 + filtro por `source_type` | busca vetorial + lexical/RRF + reranking Cohere + resposta citada |
| nvidia_knowledge | V1 expandido + V2 em andamento | catalogo cobre o brief; source_type, registry e submissao inicial para scraping criados |
| recommendations | V1 | regras deterministicas por overlap de keywords |
| briefing | V1 | briefing Markdown deterministico |
| orchestration | V1 + V2 parcial | analysis_jobs; url_ingestion_jobs para scraping -> ingestion -> embeddings |

---

## Rotas Expostas

```txt
/scraping/jobs
/scraping/results/{result_id}
/agents/runs/{run_id}
/agents/runs/{run_id}/resume
/ingestion/jobs
/embeddings/jobs
/startups
/startups/{startup_id}/evidences
/startups/{startup_id}/extract
/startups/{startup_id}/classify
/rag/search
/rag/answer
/nvidia-knowledge/technologies
/nvidia-knowledge/sources
/nvidia-knowledge/ingestion/jobs
/recommendations
/briefings
/analysis/jobs
/url-ingestion/jobs
```

---

## Banco e Migrations

Migrations existentes:

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
8d84cba84a02  indice FTS de chunks
f77998c46d08  campos estruturados em startups
1d3e7f9a2b4c  source_type em documents para separar evidencias de startups e conhecimento NVIDIA
2a7c9b8d1e5f  source_type em ingestion_jobs para preservar tipo ate o worker
5b6c7d8e9f01  url_ingestion_jobs para Orchestration V2
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
```

---

## Testes

Validacao registrada em `CLAUDE.md`:

```txt
405 passed
0 skipped com Postgres/Redis/Qdrant locais ativos
```

A suite total agora marca dependencias de integracao como `skip` explicito
quando a infra local nao esta ativa. Com Postgres/Redis/Qdrant disponiveis,
esses testes rodam normalmente.

---

## O Que Falta

Para o MVP backend macro: nada estrutural grande.

Para aderencia total ao case original:

```txt
NVIDIA Knowledge V2 - completar encadeamento scraping -> ingestion -> embeddings para documentacao NVIDIA
NVIDIA RAG Agent - Agents V10
Recommendation Agent - Agents V11 / Recommendations V3
Briefing Agent - Agents V12 / Briefing V2
Frontend
Diferencial do projeto escolhido e apresentado
Auth, observabilidade e hardening de integracao
Orchestration V2 - worker automatico e continuidade ate startup/briefing
```

---

## Proximo Passo Recomendado

```txt
NVIDIA Knowledge V2 - ingestao das fontes oficiais registradas
```

Motivo: a fundacao de escopo ja existe (`documents.source_type`,
payload `source_type` no Qdrant e filtro opcional em `/rag/search` e
`/rag/answer`) e o registry de fontes tambem ja existe em
`/nvidia-knowledge/sources`. A rota `POST /nvidia-knowledge/ingestion/jobs`
ja cria `url_ingestion_jobs` com `source_type="nvidia_knowledge"`. Falta agora
automatizar o advance desses jobs por worker/dispatcher e, depois, completar
o restante da Orchestration V2 ate startup/recommendations/briefing.
