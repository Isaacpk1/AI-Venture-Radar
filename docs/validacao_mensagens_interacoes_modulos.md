# Validacao de Mensagens e Interacoes entre Modulos

Este documento valida como mensagens e interacoes entre modulos funcionam no
monolito modular.

Validacao atualizada em 21/06/2026.

---

## 1. Regra Principal

```txt
modulo A chama contrato publico do modulo B
modulo A nao importa implementacao interna do modulo B
fila transporta identificadores
worker recebe identificador
worker chama caso de uso/factory do modulo
modulo busca dados completos no banco
```

---

## 2. Interacoes Diretas por Contrato Publico

### scraping -> agents

O scraping usa o contrato publico:

```txt
agents/application/public/semantic_investigator.py
```

Arquivo adaptador:

```txt
scraping/infrastructure/agent_adapters/agents_semantic_investigator.py
```

O scraping nao conhece grafos, LangGraph, Gemini ou persistencia interna dos
agents.

### embeddings -> ingestion

Embeddings le chunks da ingestion por contrato publico:

```txt
ingestion/application/public/ingested_reader.py
```

Adapter:

```txt
embeddings/infrastructure/ingestion_adapters/ingestion_chunk_reader.py
```

Isso permite que o worker de embeddings leia chunks sem importar models ou
repositorios internos de ingestion.

### rag -> embeddings

RAG usa os contratos publicos do modulo embeddings:

```txt
GenerateChunkEmbedding
VectorRepository.search()
```

### rag -> ingestion

RAG usa o contrato publico da ingestion para recuperar texto/fonte dos chunks:

```txt
IngestedDocumentReader.list_chunks_by_document_id()
```

### recommendations -> nvidia_knowledge

Recommendations deve consultar o catalogo NVIDIA pelo contrato publico:

```txt
nvidia_knowledge/application/public/technology_catalog.py
```

Na V1, esse contrato e atendido por um catalogo estatico. Em V2, pode passar a
usar documents/chunks/embeddings sem quebrar quem chama.

---

## 3. Mensagens por Fila

| Fila | Produtor | Worker | Mensagem |
|---|---|---|---|
| scraping | Scraping | `scraper_worker` | `job_id` |
| agents | Agents | `agent_worker` | `run_id` |
| ingestion | Ingestion | `ingestion_worker` | `job_id` |
| embeddings | Embeddings | `embedding_worker` | `job_id` |

O estado real fica nas tabelas de cada modulo, nao na fila.

---

## 4. Infraestrutura Compartilhada

Broker:

```txt
apps/api/src/shared/queue/dramatiq_broker.py
```

Usado por:

```txt
scraping
agents
ingestion
embeddings
workers/*
```

---

## 5. APIs Sincronas

Startups V1 e sincronico porque opera em dados relacionais pequenos:

```txt
POST   /startups
GET    /startups/{startup_id}
PATCH  /startups/{startup_id}
POST   /startups/{startup_id}/evidences
GET    /startups/{startup_id}/evidences
```

Agents resume tambem e sincronico:

```txt
POST /agents/runs/{run_id}/resume
```

RAG V2 tambem e sincronico:

```txt
POST /rag/search
POST /rag/answer
```

NVIDIA Knowledge V1 tambem e sincronico:

```txt
GET /nvidia-knowledge/technologies
GET /nvidia-knowledge/technologies/{slug}
```

---

## 6. Validacao por Testes

Resultado unitario recente:

```txt
297 passed
```

---

## 7. Conclusao

As fronteiras atuais estao coerentes:

```txt
workers carregam IDs
modulos chamam contratos publicos
broker e compartilhado
estado operacional fica persistido
```

Os proximos modulos devem consumir esses contratos, especialmente:

```txt
Recommendations V1 -> startups + RAG + NVIDIA Knowledge
Briefing V1 -> recommendations + evidencias citadas
```
