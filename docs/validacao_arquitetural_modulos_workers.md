# Validacao Arquitetural - Modulos e Workers

Este documento valida se o estado atual do sistema esta de acordo com a regra
arquitetural principal:

```txt
modulos sabem como fazer
workers executam trabalho pesado
filas carregam apenas identificadores
estado fica em PostgreSQL/Qdrant
```

Validacao atualizada em 21/06/2026.

---

## 1. Regra Arquitetural

O padrao esperado e:

```txt
API
-> cria ou consulta jobs
-> publica mensagem pequena na fila quando a operacao e longa
-> worker consome a mensagem
-> worker chama o modulo responsavel
-> modulo executa regra, persistencia e integracoes
```

O worker nao deve conter regra de negocio. Ele deve receber identificadores,
converter tipos serializaveis e chamar factories/casos de uso.

---

## 2. Modulos Implementados

Hoje existem seis modulos implementados:

```txt
apps/api/src/modules/scraping
apps/api/src/modules/agents
apps/api/src/modules/ingestion
apps/api/src/modules/embeddings
apps/api/src/modules/startups
apps/api/src/modules/rag
```

### Scraping

Status: de acordo.

Possui domain, application, infrastructure, presentation, factories e testes. O
trabalho pesado e executado por `workers/scraper_worker`, que chama:

```txt
ScrapingFactory.create_execute_scraping_job()
```

### Agents

Status: de acordo.

Implementado ate Agents V7:

```txt
agent_runs / agent_steps
worker por run_id
EvidenceValidationGraph
SearchPlanningGraph
checkpoint PostgreSQL para LangGraph
human-in-the-loop via GET/POST /agents/runs
```

O worker `workers/agent_worker` chama:

```txt
AgentsFactory.create_execute_agent_job()
```

### Ingestion

Status: de acordo.

Transforma `scraping_results` aprovados em `documents` e `chunks`. O worker
`workers/ingestion_worker` consome `job_id` da fila `ingestion` e chama:

```txt
IngestionFactory.create_execute_ingestion_job()
```

### Embeddings

Status: de acordo.

Gera embeddings para chunks da ingestion, persiste vetores no Qdrant e registra
jobs/chunks no PostgreSQL. O worker `workers/embedding_worker` consome `job_id`
da fila `embeddings` e chama:

```txt
EmbeddingsFactory.create_execute_embedding_job()
```

### Startups

Status: de acordo.

Operacao relacional sincrona. Nao precisa de worker em V1. Expõe CRUD basico de
startup e associacao/listagem de evidencias aprovadas.

### RAG

Status: de acordo.

Operacao sincrona em V2. Usa contratos publicos dos modulos `embeddings` e
`ingestion` para buscar evidencias semanticamente, e adapter Gemini interno ao
modulo `rag` para gerar resposta citada:

```txt
GenerateChunkEmbedding
VectorRepository.search()
IngestedDocumentReader.list_chunks_by_document_id()
RagAnswerGenerator
POST /rag/search
POST /rag/answer
```

---

## 3. Workers Existentes

```txt
workers/scraper_worker      -> fila scraping   -> job_id
workers/agent_worker        -> fila agents     -> run_id
workers/ingestion_worker    -> fila ingestion  -> job_id
workers/embedding_worker    -> fila embeddings -> job_id
```

Todos seguem a regra: mensagem pequena, worker sem regra de negocio, modulo
responsavel executando o caso de uso.

---

## 4. Infraestrutura Compartilhada

O broker Dramatiq mora em:

```txt
apps/api/src/shared/queue/dramatiq_broker.py
```

Isso evita que um modulo importe infraestrutura interna de outro modulo.

---

## 5. Validacao por Testes

Comando executado recentemente:

```txt
.\venv\Scripts\python.exe -m pytest apps\api\src\modules\startups\tests\unit apps\api\src\modules\embeddings\tests\unit apps\api\src\modules\ingestion\tests\unit apps\api\src\modules\agents\tests\unit apps\api\src\modules\scraping\tests\unit
```

Resultado:

```txt
292 passed
```

Testes de integracao existem, mas dependem de Postgres/Redis/Qdrant locais com
migrations aplicadas.

---

## 6. Pontos Ainda Pendentes

Arquiteturalmente, o sistema esta coerente. O que ainda falta e produto:

```txt
NVIDIA Knowledge V1
Recommendations V1
Briefing V1
Orchestrator / analysis job end-to-end
```

O proximo passo recomendado e `NVIDIA Knowledge V1`, porque RAG V2 ja responde
com citacoes e recommendations precisa de uma base NVIDIA citavel.
