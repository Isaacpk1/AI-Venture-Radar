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
| rag | embeddings | `GenerateChunkEmbedding`, `VectorRepository` ⚠️ |
| rag | ingestion | `IngestedDocumentReader` |
| recommendations | startups | `StartupProfileReader` |
| recommendations | nvidia_knowledge | `NvidiaTechnologyCatalog` |
| briefing | recommendations | `RecommendationsReader` |
| briefing | startups | `StartupProfileReader` |
| orchestration | recommendations | `RecommendationGenerator` |
| orchestration | briefing | `BriefingGenerator` |

⚠️ **Nota 23/06/2026:** a linha `rag -> embeddings` esta fora de
conformidade com a regra de modulo publico hoje. `GenerateChunkEmbedding` e'
uma classe concreta de `embeddings/application/use_cases/`, nao um contrato
de `application/public/` — o unico arquivo que `embeddings` declara como
importavel por outros modulos e' `embedding_service.py`
(`EmbeddingService`). Esta linha foi escrita quando isso ainda nao tinha
sido formalizado nesse nivel de rigor; nao foi revisitada depois. Detalhe
completo e fix proposto em
`docs/validacao_arquitetural_modulos_workers.md` ("Validacao 23/06/2026")
e `docs/roadmap_evolucao_tecnica_mvp.md` (Fase 5). Mantendo a linha original
acima em vez de apagar, para preservar o registro do que o codigo faz hoje.

---

## APIs Sincronas Principais

```txt
POST /startups
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
