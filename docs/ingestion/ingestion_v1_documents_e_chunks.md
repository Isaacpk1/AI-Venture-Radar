# Ingestion V1 - Documents e Chunks

Esta versao cria o modulo `ingestion`, responsavel por transformar
`scraping_results` aprovados em documentos limpos e chunks prontos para
embedding.

## 1. Objetivo

```txt
scraping_results -> ingestion_jobs -> documents -> chunks
```

O modulo nao faz scraping e nao gera embeddings. Ele prepara texto rastreavel
para as etapas seguintes.

## 2. Modelo de Dominio

`IngestionJob`:

```txt
id
scraping_result_id
status: pending | running | completed | failed
document_id
error_message
created_at
started_at
finished_at
```

`Document`:

```txt
id
ingestion_job_id
scraping_result_id
url
title
clean_text
word_count
chunk_count
created_at
```

`Chunk`:

```txt
id
document_id
chunk_index
text
word_count
char_count
created_at
```

## 3. Fluxo

```txt
POST /ingestion/jobs {"scraping_result_id": "..."}
  -> cria IngestionJob PENDING
  -> publica job_id na fila "ingestion"

ingestion_worker consome job_id
  -> ExecuteIngestionJob
  -> busca scraping_result aprovado via ScrapingResultReader
  -> limpa raw_text com TextCleaner
  -> divide texto com TextChunker
  -> salva Document
  -> salva Chunks
  -> marca job como COMPLETED com document_id
```

Em caso de erro durante execucao, o job e marcado como `FAILED` com
`error_message`.

## 4. Limpeza e Chunking

`TextCleaner`:

```txt
normaliza quebras de linha
remove caracteres de controle
colapsa espacos por linha
reduz linhas em branco consecutivas
```

`TextChunker`:

```txt
chunk_size padrao: 2000 caracteres
chunk_overlap padrao: 200 caracteres
quebra preferencial: paragrafo -> sentenca -> palavra -> limite bruto
descarta chunks menores que 50 caracteres quando o texto precisa ser dividido
```

## 5. Contratos Publicos

`IngestedDocumentReader` expoe documentos/chunks para modulos seguintes, como
`embeddings`:

```txt
get_by_scraping_result_id(scraping_result_id)
list_chunks_by_document_id(document_id)
```

O modulo `embeddings` usa esse contrato publico por meio de
`IngestionFactory.create_ingested_document_reader()`.

## 6. API

```txt
POST /ingestion/jobs
GET  /ingestion/jobs/{job_id}
```

## 7. Worker

```txt
workers/ingestion_worker
queue_name="ingestion"
max_retries=3
mensagem: job_id
```

O worker nao contem regra de negocio. Ele apenas converte o `job_id` e chama
`IngestionFactory.create_execute_ingestion_job()`.

## 8. Persistencia

Migration:

```txt
20260616_1800_3f8d1e2a9c7b_create_ingestion_tables.py
```

Tabelas:

```txt
ingestion_jobs
documents
chunks
```

## 9. Validacao

Testes unitarios existentes:

```txt
test_ingestion_entities.py
test_text_cleaner.py
test_text_chunker.py
test_create_ingestion_job.py
test_execute_ingestion_job.py
```

Testes de integracao existentes:

```txt
test_postgres_ingested_document_reader.py
```

Validacao recente do projeto:

```txt
285 testes unitarios passando
```

## 10. Limites

```txt
sem deduplicacao de documentos
sem versionamento de limpeza/chunking
sem hash de document/chunk
sem reprocessamento automatico
```

Esses pontos ficam para Ingestion V2, V3 e V5.
