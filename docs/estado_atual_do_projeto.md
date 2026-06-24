# Estado Atual do Projeto - NVIDIA Startup AI Radar

Documento de referencia do estado real em 23/06/2026.

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
| agents | V12 | Evidence, Search Planner, Extraction, Startup Classifier, NVIDIA RAG, Recommendation e Briefing (8/8 agentes do brief) |
| ingestion | V1 | documents/chunks + worker |
| embeddings | V5 | Gemini embeddings, Qdrant, worker, metricas |
| startups | V3 | dados estruturados + classificacao AI-native/AI-enabled/Non-AI |
| rag | V4 + filtro por `source_type` | busca vetorial + lexical/RRF + reranking Cohere + resposta citada |
| nvidia_knowledge | V1 expandido + V2 em andamento | catalogo cobre o brief; source_type, registry e submissao inicial para scraping criados |
| recommendations | V1 | regras deterministicas por overlap de keywords |
| briefing | V1 | briefing Markdown deterministico |
| orchestration | V1 + V2 completa | analysis_jobs; url_ingestion_jobs leva URL bruta ate startup/recommendations/briefing com worker automatico (Dramatiq) |

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
/startups?page=1&page_size=20&query=&sector=&country=&ai_maturity_level=
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
7d4f2a9c6e83  source_type em scraping_jobs para preservar origem desde a coleta
4c8a1f6e9b2d  startup_id/evidence_attached/recommendation_count/briefing_id em url_ingestion_jobs (Orchestration V2 jornada completa)
b3f6e91c7d45  indice BM25 (`pg_search`) em chunks para busca lexical (RAG V3)
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

Validacao executada em 23/06/2026:

```txt
Backend: 518 passed, 1 skipped (`pytest -q`)
Frontend: 13 passed (`npm test`)
```

A suite Python marca dependencias de integracao como `skip` explicito
quando a infra local nao esta ativa. Com Postgres/Redis/Qdrant disponiveis,
esses testes rodam normalmente.

---

## O Que Falta Para o Produto Final

Para o MVP backend macro: nada estrutural grande.

Para aderencia total ao case original:

```txt
NVIDIA Knowledge V2 - terminar de rodar o restante do registry (2/8 P0 ja validados ponta a ponta; ver docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md)
Frontend
Diferencial do projeto escolhido e apresentado
Auth, observabilidade e hardening de integracao
Recommendations V2/V4 - incorporar ai_maturity_level ao score (Startup.ai_maturity_level existe desde Startups V3, recommendations ainda nao consulta)
```

---

## Proximo Passo Recomendado

```txt
NVIDIA Knowledge V2 - terminar o lote P0 e rodar P1/P2
```

Motivo: a primeira rodada real ja confirmou o ciclo completo funcionando
(`nemo-framework-docs` e `triton-inference-server-docs` completaram
scraping -> ingestion -> embeddings, conteudo recuperavel via
`/rag/search` filtrado por `source_type=nvidia_knowledge`). No caminho,
foram corrigidos 4 bugs reais (3 em `scraping`: falso positivo de
captcha, Playwright quebrando dentro do worker, validacao evidencial
aplicada errado a fontes curadas; 1 em `embeddings`: modelo Gemini
descontinuado) — ver
`docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md`.
Falta re-testar as outras 6 fontes do lote P0 com workers limpos (o
worker precisa ser reiniciado matando processos `python.exe` orfaos pelo
lado Windows, nao so o wrapper WSL) e rodar P1/P2. Um problema de
resolucao de hostname intermitente do lado Windows (nao do codigo) ficou
pendente para o usuario resolver no ambiente. Os 8/8 agentes do brief
original ja foram entregues: Recommendation Agent (V11,
`docs/agents/agents_v11_recommendation_agent.md`) e Briefing Agent (V12,
`docs/agents/agents_v12_briefing_agent.md`) fecham o Entregavel 2 por
completo. A Orchestration V2 tambem foi fechada (URL bruta ate
startup/recommendations/briefing sem operacao manual, ver
`docs/orchestration/orchestration_v2_jornada_completa.md`).

## Prioridade Atual

O plano detalhado esta em `docs/roadmap_produto_final.md`. Com a
Orchestration V2 fechada, a prioridade imediata e o frontend (P0 #2) e, em
paralelo, terminar NVIDIA Knowledge V2 (P1 #3). Em seguida entram qualidade
das recomendacoes (`ai_maturity_level` no score), revisao/exportacao e
hardening de producao.
