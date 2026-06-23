# Roadmap Atualizado

Este roadmap substitui a leitura antiga em que `recommendations`, `briefing` e
`orchestration` ainda eram pendentes. O codigo atual ja implementa esses
modulos em V1.

---

## Estado Macro

| Area | Estado |
|---|---|
| Scraping | Entregue |
| Agents | Entregue ate V12 (8/8 do brief) |
| Ingestion | Entregue |
| Embeddings/Qdrant | Entregue |
| Startups estruturado | Entregue em slice inicial |
| RAG hibrido + reranking | Entregue |
| Catalogo NVIDIA | Entregue em V1 estatico; V2 source_type + source registry + url_ingestion_jobs entregues |
| Recommendations | Entregue em V1 deterministico |
| Briefing | Entregue em V1 deterministico |
| Orchestration | V1 entregue; V2 entregue (URL bruta ate briefing, sem etapas manuais) |
| Frontend | Nao iniciado |
| Auth/observabilidade/producao | Pendente |

---

## Prioridade de Produto

O backlog consolidado, com criterios de aceite, esta em
`docs/roadmap_produto_final.md`. A ordem de execucao e:

```txt
1. Orchestration V2 completa: URL -> startup -> briefing — ENTREGUE
2. Frontend operacional
3. NVIDIA Knowledge V2 e Recommendations V2/V4
4. Revisao humana, exportacao e ranking
5. Auth, observabilidade, CI/CD e deploy
```

O worker automatico de `url_ingestion_jobs` ja esta entregue, e a jornada
ate o briefing tambem (`docs/orchestration/orchestration_v2_jornada_completa.md`).
A prioridade agora e o Frontend (item 2).

## Proximas Entregas

### NVIDIA Knowledge V2

Ingerir documentacao oficial NVIDIA usando os modulos ja existentes:

```txt
scraping -> ingestion -> embeddings -> RAG
```

Decisao de escopo entregue: `documents.source_type`, payload `source_type` no
Qdrant e filtro opcional em RAG. Registry de fontes entregue em
`GET /nvidia-knowledge/sources`; submissao para Orchestration V2 entregue em
`POST /nvidia-knowledge/ingestion/jobs`. O default continua
`startup_evidence`; docs NVIDIA devem entrar como `nvidia_knowledge`.

O worker/dispatcher para reenfileirar `url_ingestion_jobs` ja foi entregue.
Faltam validar as seis fontes P0 restantes e rodar os lotes P1/P2.

### Agents V10-V12 - Entregues

NVIDIA RAG, Recommendation e Briefing Agents estao implementados. A lacuna
atual e integra-los ao fluxo principal — hoje o fluxo automatico da
Orchestration V2 usa os geradores deterministicos
(`recommendations`/`briefing` V1), nao os agentes; eles continuam
acionaveis so pela fila generica `agent_runs`.

### Orchestration V2 - ENTREGUE

Entrada por URL bruta, ponta a ponta:

```txt
URL -> scraping -> ingestion -> embeddings -> startup/extract/classify
-> recommendations -> briefing
```

Ver `docs/orchestration/orchestration_v2_jornada_completa.md`.

### Frontend

Interface para operar o fluxo e visualizar resultados. Proxima prioridade.

---

## Trilhas Paralelas

```txt
hardening de integracao
auth/autorizacao
observabilidade
custos de LLM
exportacao PDF/HTML do briefing
revisao humana de recommendations/briefing
```
