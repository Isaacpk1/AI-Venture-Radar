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
| Embeddings V1 | Futuro | Contratos e provider fake |
| Embeddings V2 | Futuro | Provider real de embedding |
| Embeddings V3 | Futuro | Persistencia no Qdrant |
| Embeddings V4 | Futuro | Batch worker |
| Embeddings V5 | Futuro | Reembedding e metricas |

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

- detectar chunks que mudaram;
- reprocessar embeddings;
- medir custo;
- medir latencia;
- registrar modelo usado e dimensao.
