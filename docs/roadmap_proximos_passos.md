# Roadmap Atualizado

Este roadmap substitui a leitura antiga em que `recommendations`, `briefing` e
`orchestration` ainda eram pendentes. O codigo atual ja implementa esses
modulos em V1.

---

## Estado Macro

| Area | Estado |
|---|---|
| Scraping | Entregue |
| Agents base | Entregue ate V9 |
| Ingestion | Entregue |
| Embeddings/Qdrant | Entregue |
| Startups estruturado | Entregue em slice inicial |
| RAG hibrido + reranking | Entregue |
| Catalogo NVIDIA | Entregue em V1 estatico; V2 source_type + source registry + url_ingestion_jobs entregues |
| Recommendations | Entregue em V1 deterministico |
| Briefing | Entregue em V1 deterministico |
| Orchestration | Entregue em V1 para startup existente |
| Frontend | Nao iniciado |
| Auth/observabilidade/producao | Pendente |

---

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

Proximo passo desta entrega: criar worker/dispatcher para reenfileirar
`url_ingestion_jobs` e chamar advance ate embedding concluido.

### Agents V10 - NVIDIA RAG Agent

Grafo LangGraph que consulta a base NVIDIA com citacoes.

### Agents V11 / Recommendations V3

Recommendation Agent usando `RecommendationGenerator` como tool e RAG NVIDIA
como contexto adicional.

### Agents V12 / Briefing V2

Briefing Agent usando `BriefingGenerator` como tool, melhorando a prosa sem
perder rastreabilidade.

### Orchestration V2

Entrada por URL bruta:

```txt
URL -> scraping -> ingestion -> embeddings -> startup/extract/classify
-> recommendations -> briefing
```

### Frontend

Interface para operar o fluxo e visualizar resultados.

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
