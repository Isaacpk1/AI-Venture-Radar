# Estado Atual do Projeto - NVIDIA Startup AI Radar

Documento de referencia do estado real do sistema em 21/06/2026.

---

## 1. Visao Geral

O NVIDIA Startup AI Radar e uma pipeline para coletar evidencias publicas sobre
startups, validar qualidade, transformar conteudo em base consultavel e gerar,
nas proximas etapas, recomendacoes NVIDIA com fontes.

O projeto segue um monolito modular com workers separados para tarefas longas.

---

## 2. Modulos Implementados

| Modulo | Estado | Versao atual |
|---|---|---|
| scraping | implementado e maduro | Scraping V8 |
| agents | implementado | Agents V7 |
| ingestion | implementado | Ingestion V1 + worker |
| embeddings | implementado | Embeddings V5 |
| startups | implementado | Startups V1 |
| rag | implementado | RAG V2 |

---

## 3. Scraping - V8

Responsabilidade:

```txt
URL -> coleta -> validacao tecnica/textual/evidencial -> scraping_results
```

Camadas:

```txt
domain/         ScrapingJob, ScrapingAttempt, ScrapingResult
application/    pipeline, estrategia, casos de uso
infrastructure/ BeautifulSoup, Playwright, Trafilatura, validadores,
                Gemini semantic validator, adapter para agents, PostgreSQL,
                Dramatiq
presentation/   POST /scraping/jobs, GET /scraping/jobs/{id},
                GET /scraping/results/{id}
worker/         workers/scraper_worker
```

Tabelas:

```txt
scraping_jobs
scraping_attempts
scraping_results
```

---

## 4. Agents - V7

Responsabilidade:

```txt
orquestrar fluxos com LangGraph e registrar AgentRun/AgentStep
```

Entregas:

```txt
EvidenceValidationGraph
SearchPlanningGraph
agent_worker
agent_runs e agent_steps no PostgreSQL
checkpoint LangGraph no PostgreSQL
human-in-the-loop com GET /agents/runs/{id}
resume com POST /agents/runs/{id}/resume
```

Status:

```txt
pending -> running -> completed
                   -> failed
                   -> waiting_human_review -> running -> completed/failed
```

Tabelas:

```txt
agent_runs
agent_steps
checkpoint_migrations
checkpoints
checkpoint_blobs
checkpoint_writes
```

Documento atual: `docs/agents/agents_v7_human_in_the_loop.md`.

---

## 5. Ingestion - V1

Responsabilidade:

```txt
scraping_results aprovados -> documents -> chunks
```

Fluxo:

```txt
POST /ingestion/jobs {scraping_result_id}
  -> IngestionJob PENDING
  -> fila "ingestion"
  -> ingestion_worker
  -> TextCleaner
  -> TextChunker
  -> Document + Chunks
```

Tabelas:

```txt
ingestion_jobs
documents
chunks
```

Documento: `docs/ingestion/ingestion_v1_documents_e_chunks.md`.

---

## 6. Embeddings - V5

Responsabilidade:

```txt
chunks -> embeddings -> Qdrant
```

Entregas:

```txt
EmbeddingService fake e Gemini
VectorRepository Qdrant
GenerateChunkEmbedding
UpsertChunkEmbedding
EmbeddingJob e EmbeddingJobChunk
embedding_worker
metricas operacionais por job/chunk
base de reembedding por content_hash
```

Tabelas:

```txt
embedding_jobs
embedding_job_chunks
```

Qdrant guarda vetores com payload minimo:

```txt
chunk_id
document_id
source_url
model_name
```

Documentos:

```txt
docs/embeddings/embeddings_v4_worker_em_lote.md
docs/embeddings/embeddings_v5_metricas_reembedding.md
```

---

## 7. Startups - V1

Responsabilidade:

```txt
representacao relacional basica de startups e evidencias associadas
```

Entregas:

```txt
Startup
StartupEvidence
repositorios PostgreSQL
POST /startups
GET /startups/{id}
PATCH /startups/{id}
POST /startups/{id}/evidences
GET /startups/{id}/evidences
```

Tabelas:

```txt
startups
startup_evidences
```

Documento: `docs/startups/startups_v1_modelo_relacional.md`.

---

## 8. RAG - V2

Responsabilidade:

```txt
pergunta -> evidencias recuperadas -> resposta com citacoes
```

Entregas:

```txt
Retriever
SearchEvidence
AnswerQuestion
RagAnswerGenerator
POST /rag/search
POST /rag/answer
reuso de GenerateChunkEmbedding
reuso de VectorRepository.search()
reuso de IngestedDocumentReader
adapter Gemini via LangChain em rag/infrastructure/llm
validacao estrutural de resposta e citacoes
```

Documentos:

```txt
docs/rag/rag_v1_busca_semantica.md
docs/rag/rag_v2_resposta_com_citacoes.md
```

---

## 9. Infraestrutura Compartilhada

```txt
PostgreSQL  -> fonte da verdade relacional
Redis       -> broker Dramatiq
Qdrant      -> banco vetorial
FastAPI     -> API
Dramatiq    -> workers
LangGraph   -> grafos de agents
```

Broker compartilhado:

```txt
apps/api/src/shared/queue/dramatiq_broker.py
```

Workers:

```txt
workers/scraper_worker
workers/agent_worker
workers/ingestion_worker
workers/embedding_worker
```

---

## 10. Migrations

| Revisao | Descricao |
|---|---|
| `f3f7f3959ccc` | scraping tables |
| `a41c96d32e57` | content_hash unico em scraping_results |
| `d8e4a9c1b672` | campos de auditoria de agent em attempts |
| `7c9f2a1b4d6e` | agent_runs e agent_steps |
| `9e1f3b5c8a2d` | checkpoint LangGraph |
| `3f8d1e2a9c7b` | ingestion tables |
| `b7e2c4f8a1d3` | embedding tables |
| `c19a4e5f6b20` | startup tables |

Head esperado:

```txt
c19a4e5f6b20
```

---

## 11. Testes

Validacao unitaria recente:

```txt
292 passed
```

Observacao: testes de integracao existem, mas dependem de Postgres, Redis e
Qdrant locais com migrations aplicadas.

---

## 12. O Que Ainda Falta

Modulos ainda nao implementados:

```txt
nvidia_knowledge
recommendations
briefing
orchestration / analysis job end-to-end
frontend
auth/usuarios
observabilidade de producao
```

---

## 13. Proximo Passo Recomendado

```txt
NVIDIA Knowledge V1 - catalogo inicial de tecnologias NVIDIA
```

Motivo:

```txt
scraping gera evidencias
ingestion gera documents/chunks
embeddings gera vetores no Qdrant
startups organiza entidades/evidencias
rag recupera evidencias e gera resposta com citacoes
```

Falta agora criar conhecimento NVIDIA estruturado para que recommendations e
briefing tenham base tecnica citavel.

---

## 14. Fluxo Para MVP

```txt
1. coletar evidencia publica de uma startup        -> implementado
2. validar se a evidencia e util                   -> implementado
3. persistir conteudo aprovado                     -> implementado
4. transformar conteudo em documents/chunks        -> implementado
5. gerar embeddings                                -> implementado
6. buscar evidencias semanticamente                -> implementado
7. responder perguntas com citacoes                -> implementado
8. consolidar perfil da startup                    -> basico implementado
9. consultar conhecimento NVIDIA                   -> pendente
10. recomendar tecnologias NVIDIA                  -> pendente
11. gerar briefing executivo com fontes            -> pendente
```

---

## 15. Referencias

| Documento | Caminho |
|---|---|
| Indice | `docs/README.md` |
| Roadmap geral | `docs/roadmap_proximos_passos.md` |
| Arquitetura global | `docs/arquitetura_global_monolito_modular_workers.md` |
| Validacao arquitetural | `docs/validacao_arquitetural_modulos_workers.md` |
| Mensagens entre modulos | `docs/validacao_mensagens_interacoes_modulos.md` |
| Roadmap RAG | `docs/rag/roadmap_rag.md` |
| Lacunas para MVP | `docs/proximos_passos_mvp.md` |
