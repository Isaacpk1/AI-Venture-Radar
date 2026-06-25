# Estado Atual do Projeto - NVIDIA Startup AI Radar

Documento de referencia do estado real em 24/06/2026. Para o detalhe
completo de cada entrega, ver `CLAUDE.md` secao "Authoritative Current
State" (sempre a fonte mais atualizada) e o "Module version history".

---

## Resumo

O backend modular do MVP esta implementado de ponta a ponta:

```txt
scraping -> ingestion -> embeddings -> startups -> rag -> recommendations
-> briefing -> orchestration
```

Tambem existem os 8 agentes do brief original (LangGraph): Evidence
Validation, Search Planner, Extraction, Startup Classifier, NVIDIA RAG,
Recommendation e Briefing. Os dois ultimos ja tem consumidor sincrono real
dentro de `orchestration`. O frontend (Next.js) cobre a jornada
URL -> job -> resultado da startup, portfolio paginado de startups,
historico global de jobs, chatbot sobre NVIDIA Knowledge, badge de fit,
evidencia clicavel por recomendacao e export do briefing em PDF —
Frontend V3 esta completo.

---

## Modulos Implementados

| Modulo | Versao atual | Observacao |
|---|---|---|
| scraping | V8 | pipeline com validacao deterministica, Gemini e agent review |
| agents | V12 | Evidence, Search Planner, Extraction, Startup Classifier, NVIDIA RAG, Recommendation e Briefing (8/8 agentes do brief) |
| ingestion | V1 | documents/chunks + worker (worker entregue junto da V1) |
| embeddings | V5 | metricas operacionais por job/chunk + cache por `content_hash` + guarda de schema do Qdrant |
| startups | V3 (slice inicial) | dados estruturados + classificacao AI-native/AI-enabled/Non-AI + `ListStartups` paginado |
| rag | V4 | busca vetorial + lexical (BM25 via `pg_search`) com RRF + reranking Cohere + resposta citada |
| nvidia_knowledge | V1 + V2 completo | catalogo cobre o brief; 20/20 fontes do registry processadas, 17/20 com conteudo recuperavel |
| recommendations | V2 | regras deterministicas + justificativa fundamentada via RAG (NVIDIA Knowledge), com fallback deterministico |
| briefing | V3 | template executivo + secao "Contexto NVIDIA" via RAG (extensao V1) + export em PDF real (Playwright+Jinja2, V3) |
| orchestration | V1 + V2 completa | analysis_jobs; url_ingestion_jobs leva URL bruta ate startup/recommendations/briefing com worker automatico (Dramatiq), sem operacao manual; historico global paginado (`GET /url-ingestion/jobs`) |
| frontend | V3 completa | jornada URL->job->resultado (V2) + portfolio paginado, historico global de jobs, badge de fit, evidencia clicavel, chatbot NVIDIA Knowledge e export PDF (V3) |

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
/briefings/{briefing_id}/export
/analysis/jobs
/url-ingestion/jobs
/url-ingestion/jobs?page=1&page_size=20&status=&source_type=
```

---

## Banco e Migrations

Migrations existentes (head atual: `b3f6e91c7d45` — sem mudanca nesta
entrega, o historico de jobs e o export de PDF nao precisaram de schema
novo):

```txt
f3f7f3959ccc  scraping tables
a41c96d32e57  content_hash unico em scraping_results
d8e4a9c1b672  campos de auditoria de agent em attempts
7c9f2a1b4d6e  agent_runs e agent_steps
9e1f3b5c8a2d  checkpoint LangGraph
3f8d1e2a9c7b  ingestion tables
b7e2c4f8a1d3  embedding tables (ja inclui campos de metricas da V5, commit unico)
c19a4e5f6b20  startup tables
f90193dc1578  recommendations
782e2cbdbfab  briefings
2e85accbd38f  analysis_jobs
3ca1a725713e  classificacao em startups
8d84cba84a02  indice FTS de chunks (substituido pela b3f6e91c7d45)
f77998c46d08  campos estruturados em startups
1d3e7f9a2b4c  source_type em documents para separar evidencias de startups e conhecimento NVIDIA
2a7c9b8d1e5f  source_type em ingestion_jobs para preservar tipo ate o worker
5b6c7d8e9f01  url_ingestion_jobs para Orchestration V2
7d4f2a9c6e83  source_type em scraping_jobs para preservar origem desde a coleta
4c8a1f6e9b2d  startup_id/evidence_attached/recommendation_count/briefing_id em url_ingestion_jobs (Orchestration V2 jornada completa)
b3f6e91c7d45  indice BM25 (`pg_search`) em chunks para busca lexical (RAG V3, extensao)
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

Validacao executada em 24/06/2026 com infra local ativa
(Postgres/Redis/Qdrant via `infra/docker-compose.yml`):

```txt
Backend: 524 passed, 1 skipped (`pytest apps/api/src/modules/ apps/api/src/shared/ -q`)
  - o skip e o teste Ragas opt-in (RUN_RAGAS_EVAL=1 nao definido)
Frontend: 25 passed (`npm test` em apps/web/)
```

A suite Python marca dependencias de integracao como `skip` explicito
quando a infra local nao esta ativa. Com Postgres/Redis/Qdrant
disponiveis, esses testes rodam normalmente. O teste de PDF
(`test_jinja_playwright_pdf_renderer.py`) precisa so do Chromium do
Playwright, ja instalado — nao depende de Postgres/Redis/Qdrant.

Validado tambem fora da suite automatizada, via `httpx.AsyncClient`
direto contra a app ASGI real: criar startup -> recommendations ->
briefing -> `GET /url-ingestion/jobs` (200, total real) ->
`GET /briefings/{id}/export` (200, PDF real de 28KB, `%PDF-1.4`) ->
`POST /rag/answer` (200, resposta real do Gemini). `next build` e
`tsc --noEmit` sem erro.

---

## O Que Falta Para o Produto Final

Para o MVP backend macro: nada estrutural grande. Frontend V3 (todo o
escopo do roadmap original de frontend que importava pro caso) tambem
esta completo agora.

Para aderencia total ao case original (ver CLAUDE.md secao "Pending" para
o detalhe e ordem de prioridade):

```txt
Sincronia Qdrant<->Postgres (payload do Qdrant reupsert quando
Document/ScrapingResult mudar) - decidido, falta implementar; risco
pratico baixo hoje (sem fluxo de edicao de evidencia ainda)
rapidfuzz para dedup de startups por nome/website - decidido, falta
calibrar o limiar de similaridade e implementar
Descoberta de startups por fontes gratuitas (StartSe, Distrito, Endeavor
etc.) - zero orcamento, ver docs/scraping/roadmap_scraping.md
Frontend V4 (Recharts, comparacao, fila em lote) - precisa de endpoints
agregados novos no backend (GROUP BY), nenhum item acima cria isso
Auth, CI/CD, deploy e backup do Qdrant - fora de escopo deliberadamente
(decidido 23/06/2026: este projeto continua case/demo, nao alvo de
producao; ver tabela "Decisoes ja resolvidas" em
docs/decisoes_pendentes.md, linha "Projeto e' demo ou produto real?",
movida para docs/roadmap_produto_final.md)
```

NVIDIA Knowledge V2, Orchestration V2 (URL bruta ate briefing), Frontend
V3 completo e P3 (diferencial do case, decidido + implementado) ja estao
prontos — nao aparecem mais como pendencia nesta lista.
`docs/decisoes_pendentes.md` nao tem pergunta em aberto.

---

## Proximo Passo Recomendado

```txt
Sincronia Qdrant<->Postgres ou calibracao do limiar do rapidfuzz para
dedup de startups — sem ordem decidida entre os dois. Descoberta de
startups por fontes gratuitas pode entrar em paralelo se sobrar
capacidade.
```

Motivo: todos os itens de maior prioridade do roadmap original
(`docs/roadmap_produto_final.md`) ja foram fechados — NVIDIA Knowledge V2
(20/20 fontes, 17/20 com conteudo), Orchestration V2 (URL bruta ate
startup/recommendations/briefing, sem operacao manual), Frontend V3
completo (navegacao/historico, transparencia, chatbot, export) e P3
(diferencial "rastreabilidade ponta a ponta" — decidido e ja
implementado: citacoes NVIDIA como link Markdown real + frontend
renderiza Markdown de verdade no briefing, justificativa e chatbot). O
que resta e' so o backlog secundario, sem ordem de prioridade definida
entre os itens.
