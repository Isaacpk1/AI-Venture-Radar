# Roadmap Atualizado

Atualizado em 26/06/2026. Este roadmap substitui leituras antigas em que `recommendations`, `briefing`, `orchestration`, `frontend` ou descoberta de startups ainda apareciam como pendentes.

---

## Estado Macro

| Area | Estado |
|---|---|
| Scraping | Entregue ate V8 |
| Agents | Entregue ate V12 (8/8 agentes do brief) |
| Ingestion | Entregue |
| Embeddings/Qdrant | Entregue |
| Startups estruturado | Entregue ate V4 |
| RAG hibrido + reranking | Entregue |
| Catalogo NVIDIA | NVIDIA Knowledge V2 entregue |
| Recommendations | V3 entregue: RAG grounding, confidence/complexity e stats |
| Briefing | V3 entregue: RAG grounding + export PDF |
| Orchestration | V2.1 entregue: URL bruta ate briefing, com primeira rodada de enriquecimento por dominio |
| Frontend | V1/V2/V3/V4/V5 entregues |
| Startup Discovery | V1 entregue em 3 hubs publicos |
| Auth/observabilidade/producao | Fora de escopo do demo, exceto fundacoes ja existentes |

---

## Prioridade De Produto

O backlog consolidado, com criterios de aceite, esta em `docs/roadmap_produto_final.md`. A ordem atual e:

```txt
1. Validar a chain de enriquecimento com Tavily real e calibrar ranking/allowlist.
2. Expandir Startup Discovery para mais hubs gratuitos.
3. Hardening de producao apenas se o projeto deixar de ser demo.
```

---

## Entregas Fechadas

### Orchestration V2

```txt
URL -> scraping -> ingestion -> embeddings -> startup/extract/classify
-> recommendations -> briefing
```

Entregue com `url_ingestion_jobs`, worker automatico, historico paginado e limpeza best-effort de vetores orfaos no Qdrant em re-scrape.

### Orchestration V2.1

Primeira fatia da chain de enriquecimento entregue: quando a extracao deixa
`founders`, `funding_stage` ou `customers` vazios, a orquestracao agenda ate
2 jobs filhos no mesmo dominio da startup, com `parent_job_id`,
`enrichment_round` e limite de uma rodada para evitar loop.

### Orchestration V2.2

Busca externa opcional entregue: `agents` expoe `SearchExecutorPort` com
`TavilySearchExecutor`, e `AdvanceUrlIngestionJob` tenta URLs externas
planejadas pelo Search Planner antes do fallback do mesmo dominio. Sem
`TAVILY_API_KEY`, o fluxo continua local com o fallback por dominio.

### NVIDIA Knowledge V2

P0+P1+P2 completos: 20/20 fontes processadas, 17/20 com conteudo recuperavel via RAG. Os gaps restantes sao limitacoes de ambiente ou necessidade de fallback pago (Firecrawl), nao bloqueios do MVP.

### Recommendations V3

O modulo gera recomendacoes deterministicas, fundamenta justificativas via RAG NVIDIA quando ha contexto, persiste `confidence` e `complexity`, e expoe `GET /recommendations/stats` para o dashboard.

### Frontend V4

Interface para operar o fluxo e visualizar resultados: submissao de URL, job detail, startup detail, portfolio, historico, chat NVIDIA Knowledge, export PDF, dashboard, comparacao de startups e fila em lote.

### Frontend V5

Revisao humana simples entregue para recommendations e briefings, sem auth completa.

### Startup Discovery V1

Descoberta automatica em InovAtiva Brasil, Abstartups e 100 Open Startups, com `startup_discovery_runs` persistido e URLs submetidas ao pipeline de `url_ingestion_jobs`.

---

## Trilhas Paralelas

```txt
chain de enriquecimento com busca externa
observabilidade mais profunda dentro dos use cases
expansao gradual dos hubs de descoberta
```
