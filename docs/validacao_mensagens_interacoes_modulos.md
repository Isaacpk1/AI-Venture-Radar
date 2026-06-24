# Validacao de Mensagens e Interacoes entre Modulos

Validacao atualizada em 22/06/2026.

---

## Filas

| Fila | Produtor | Worker | Payload |
|---|---|---|---|
| scraping | scraping | scraper_worker | job_id |
| agents | agents | agent_worker | run_id |
| ingestion | ingestion | ingestion_worker | job_id |
| embeddings | embeddings | embedding_worker | job_id |
| url_ingestion | orchestration | orchestration_worker | job_id |

Regra: fila carrega identificador; o worker busca o estado completo no banco e
chama factory/use case.

---

## Contratos Publicos

| Origem | Destino | Contrato |
|---|---|---|
| scraping | agents | `SemanticInvestigator` |
| startups | agents | `ExtractionService`, `StartupClassifierService` |
| embeddings | ingestion | `IngestedDocumentReader` |
| rag | embeddings | `EmbeddingService`, `VectorRepository` |
| rag | ingestion | `IngestedDocumentReader` |
| recommendations | startups | `StartupProfileReader` |
| recommendations | nvidia_knowledge | `NvidiaTechnologyCatalog` |
| briefing | recommendations | `RecommendationsReader` |
| briefing | startups | `StartupProfileReader` |
| orchestration | recommendations | `RecommendationGenerator`, `RecommendationJustificationUpdater` |
| orchestration | briefing | `BriefingGenerator`, `BriefingContentUpdater` |
| orchestration | agents | `RecommendationAgentService`, `BriefingAgentService` (23/06/2026) |
| agents | recommendations | `RecommendationGenerator`, `RecommendationJustificationUpdater` |
| agents | briefing | `BriefingGenerator`, `BriefingContentUpdater` |

✅ **Corrigido em 23/06/2026:** a linha `rag -> embeddings` chegou a ficar
fora de conformidade (listava `GenerateChunkEmbedding`, classe concreta de
`embeddings/application/use_cases/`, em vez de so o contrato publico
`EmbeddingService`). Corrigido com um adapter novo,
`rag/infrastructure/embeddings_adapters/embeddings_query_embedder.py`
(`EmbeddingsQueryEmbedder`, implementa a porta interna `EmbeddingGenerator`
de `rag/application/ports.py`), mesmo padrao do `IngestionChunkReader` em
`embeddings`. Detalhe completo em
`docs/validacao_arquitetural_modulos_workers.md` ("Validacao 23/06/2026")
e `docs/roadmap_evolucao_tecnica_mvp.md` (Fase 5).

---

## APIs Sincronas Principais

```txt
POST /startups
GET  /startups?page=1&page_size=20
POST /startups/{id}/extract
POST /startups/{id}/classify
POST /rag/answer
GET  /nvidia-knowledge/technologies
POST /recommendations
POST /briefings
POST /analysis/jobs
```

---

## Proximas Interacoes A Criar

```txt
nvidia_knowledge V2 -> scraping/ingestion/embeddings
NVIDIA RAG Agent -> rag/public ou retriever especializado
Recommendation Agent -> recommendations/public + NVIDIA RAG Agent
Briefing Agent -> briefing/public + recommendations/public
```
