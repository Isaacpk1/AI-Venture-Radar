# Roadmap do Modulo Embeddings

O modulo `embeddings` transforma chunks textuais em vetores e sincroniza esses
vetores com o Qdrant.

Ele nao decide resposta final. Ele cria a camada de busca semantica.

---

## Objetivo do Modulo

```txt
chunks -> embeddings -> Qdrant
```

PostgreSQL continua sendo a fonte de verdade para documentos, chunks e status.
Qdrant guarda vetores e metadados de busca.

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| Embeddings V1 | Implementado | Contratos e provider fake |
| Embeddings V2 | Implementado | Provider real de embedding |
| Embeddings V3 | Implementado | Persistencia no Qdrant |
| Embeddings V4 | Implementado | Batch worker |
| Embeddings V5 | Implementado | Base de reembedding e metricas operacionais |

---

## Embeddings V1 - Contratos e Fake

Entregaveis:

- modulo `apps/api/src/modules/embeddings`;
- contrato publico `EmbeddingService`;
- DTOs para entrada e saida;
- provider fake deterministicos para testes;
- caso de uso `GenerateChunkEmbedding`;
- testes unitarios.

Criterio de pronto:

```txt
um chunk consegue gerar um vetor fake estavel em teste
```

---

## Embeddings V2 - Provider Real

Entregaveis:

- provider real de embedding;
- configuracao por ambiente;
- tratamento de erro de API;
- controle basico de dimensao do vetor;
- testes com fake e contrato.

Provider pode ser Gemini, Cohere ou outro. A decisao deve ficar escondida atras
do contrato `EmbeddingService`.

---

## Embeddings V3 - Qdrant

Entregaveis:

- colecao no Qdrant;
- `VectorRepository`;
- upsert de vetores;
- metadados com `chunk_id`, `document_id`, `source_url`;
- busca semantica basica.

---

## Embeddings V4 - Worker em Batch

Entregaveis:

- `workers/embedding_worker`;
- fila `embeddings`;
- job de embeddings por lote;
- retry/backoff;
- status por chunk.

---

## Embeddings V5 - Reembedding e Metricas

Entregaveis:

- registrar `content_hash` por chunk processado;
- reprocessar embeddings via novo `EmbeddingJob` para o mesmo documento;
- medir latencia por chunk e latencia total do job;
- medir caracteres e tokens estimados de entrada;
- registrar modelo usado e dimensao por chunk;
- expor agregados do job na API.

Criterio de pronto:

```txt
um job de embeddings concluido mostra quantos chunks venceram/falharam,
qual volume de entrada foi processado e quais metadados de embedding foram
gravados por chunk
```

Observacao: custo monetario real ainda nao e medido porque o provider atual
nao retorna preco nem uso real de tokens. A V5 registra tokens estimados para
observabilidade inicial; custo real fica para uma futura camada de billing por
provider.

---

## Proximo passo recomendado

```txt
RAG V1 - busca semantica sobre chunks vetorizados
```

Motivo: scraping, ingestion, embeddings e startups basico ja formam a primeira
linha `URL -> evidencia validada -> documento/chunks -> vetores -> startup`.
Agora o sistema precisa recuperar esses chunks semanticamente e retornar
evidencias citaveis.
