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

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

Confirmado em `infrastructure/gemini/gemini_embedding_provider.py` e
`infrastructure/qdrant/qdrant_vector_repository.py`: o modelo ja trocou uma
vez (`models/text-embedding-004` -> `models/gemini-embedding-001`, ver
extensao da V4 no `CLAUDE.md`) sem nenhum campo de versao gravado no Qdrant
— vetores antigos e novos convivem na mesma colecao sem distincao.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| Troca de modelo de embedding nao deixa rastro no vetor armazenado | gravar `embedding_model` no payload do Qdrant a cada upsert (campo novo, sem lib nova) | Base para uma futura V6 de migracao de modelo sem busca quebrada | Baixo |
| Chunk identico (mesmo `content_hash`) e reembeddido do zero se o job rodar de novo | cache por `content_hash` do chunk antes de chamar o provider — pula a chamada Gemini se o hash ja tem vetor salvo — **concluido em 23/06/2026** | Reduz custo de API, complementa a V5 (metricas) | Baixo — so consulta antes de gerar |
| Tokens de entrada sao estimados (`estimate_input_tokens()`), nao o uso real reportado pela API | usar o uso real de tokens que a resposta do LangChain/Gemini ja retorna (`usage_metadata`), em vez da heuristica | Fecha o gap que a V5 ja deixou registrado como limite conhecido | Baixo — dado ja vem na resposta, falta so ler e logar (via `shared/logging`, Fase 0 ja entregue) |

Nao adotar embeddings locais (Hugging Face/sentence-transformers) nem trocar
de provider agora: o ponto fraco real e observabilidade/cache em torno do
provider atual, nao o provider em si.

**Cache por content_hash — concluido em 23/06/2026:**
`EmbeddingJobChunkRepository.find_completed_by_content_hash()` (novo,
filtra por hash + `model_name` — nunca reusa vetor de um modelo diferente
do configurado) + `VectorRepository.get_by_chunk_id()` (novo, recupera
vetor existente do Qdrant) + `UpsertChunkEmbedding.execute(...,
cached_chunk_id=...)` (pula a chamada ao provider quando ha cache hit).
`ExecuteEmbeddingJob` consulta o cache antes de cada chunk. Testado:
2 chunks com texto identico em documentos diferentes geram 1 unica chamada
ao provider de embedding.
