# Roadmap de Evolucao Tecnica para um MVP Solido

Criado em 23/06/2026, a partir de
`docs/diagnostico_fraquezas_e_tecnologias_recomendadas.md`. Aquele
documento foi para decisao (o que existe, o que falta, o que cada
tecnologia resolve). Este documento e para execucao: fases ordenadas,
entregaveis e criterio de pronto. Nada aqui foi implementado ainda.

## 1. O que significa "MVP realmente bom" aqui

Nao e adicionar mais features de produto. E fechar a lacuna entre "o
pipeline funciona uma vez, manualmente verificado" e "o pipeline e
confiavel, medido e debugavel":

```txt
Toda chamada de LLM tem custo, latencia e prompt/resposta rastreaveis.
Toda recomendacao gerada tem um score que reflete sinal real, nao
coincidencia de substring.
A qualidade da busca RAG e medida, nao assumida.
Uma falha em qualquer etapa do pipeline aparece em log com IDs de
correlacao, sem precisar ler codigo para descobrir o que aconteceu.
```

As 5 fases abaixo levam o projeto desse ponto A para esse ponto B na
ordem que minimiza retrabalho (medir antes de trocar tecnologia,
observar antes de avaliar).

## 2. Fase 0 — Fundacao de observabilidade

Sem isso, as fases seguintes nao tem como ser validadas objetivamente.

Entregaveis:

- `apps/api/src/shared/logging/` — logger estruturado (JSON), helper que
  injeta `request_id`/`job_id`/`startup_id`/`document_id`/`agent_run_id`
  conforme a regra 10 do CLAUDE.md;
- instrumentar pelo menos os use cases de entrada de cada modulo
  (scraping, ingestion, embeddings, startups, recommendations, briefing,
  orchestration) e os 5 workers — log de inicio, fim e falha de cada job;
- Langfuse integrado via callback handler do LangChain em todos os
  pontos que ja usam `ChatGoogleGenerativeAI`/`GoogleGenerativeAIEmbeddings`
  (rag, embeddings, agents V8-V12) — sem reescrever prompts ou grafos;
- variavel de ambiente nova: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`,
  `LANGFUSE_HOST` (self-hosted via docker-compose ou cloud);
- dashboard minimo: custo e latencia por `agent_run_id` e por job.

Criterio de pronto:

```txt
uma falha em qualquer etapa do pipeline pode ser diagnosticada lendo
logs e o painel do Langfuse, sem abrir codigo nem consultar o Postgres
na mao.
```

Dependencias: nenhuma. Pode comecar imediatamente, em paralelo com a
Fase 1.

## 3. Fase 1 — Corrigir Recommendations

Bug confirmado em `docs/diagnostico_fraquezas_e_tecnologias_recomendadas.md`
secao 2.3 (todas as recomendacoes saindo em 27% de fit por coincidencia
de substring, nao por sinal real).

Entregaveis:

- `orchestration`/`startups`: preencher `sector`/`description` ao criar
  a `Startup` automaticamente pelo fluxo de URL (hoje ficam `None`
  sempre nesse caminho);
- `recommendations/domain/policies.py::match_technologies()`: trocar
  substring puro por regex com `\b...\b` (word boundary), eliminando
  falsos positivos como "Escale" casando com o alias "scale";
- revisar `KEYWORD_ALIASES` apos a correcao de word boundary — alguns
  aliases foram adicionados para compensar o substring puro e podem nao
  ser mais necessarios, ou podem precisar de ajuste;
- testes novos cobrindo o caso real encontrado (pagina de marketing em
  portugues vs. catalogo em ingles) e o falso positivo do alias.

Criterio de pronto:

```txt
rodar a mesma URL de teste (https://dadosfera.com.br) e obter scores que
variam de fato entre as tecnologias recomendadas, refletindo overlap
real de keywords, nao 27% uniforme.
```

Dependencias: nenhuma. Pode comecar imediatamente, em paralelo com a
Fase 0.

## 4. Fase 2 — Linha de base de qualidade com Ragas

Medir antes de trocar qualquer tecnologia de busca (BM25, modelo de
rerank). Sem isso, a Fase 3 e aposta.

Entregaveis:

- dataset golden de perguntas+respostas esperadas sobre o conteudo ja
  ingerido em NVIDIA Knowledge (mesmo que pequeno no inicio — crescer
  junto com mais fontes P0/P1 sendo processadas);
- teste de integracao novo em `rag` usando Ragas (`faithfulness`,
  `context_precision`, `context_recall`, `answer_relevancy`) contra
  `SearchEvidence`/`AnswerQuestion`;
- numero de baseline registrado em doc (nao so no CI) para comparar
  depois da Fase 3: recall do `ts_rank` atual, score de fidelidade da
  resposta gerada.

Criterio de pronto:

```txt
existe um numero objetivo de qualidade de busca e de resposta hoje,
antes de qualquer mudanca em BM25 ou reranking.
```

Dependencias: idealmente mais fontes do NVIDIA Knowledge V2 ingeridas
(hoje 2/8 P0); pode comecar com o que existe e crescer depois.

### Fase 2 — concluida em 23/06/2026

```txt
faithfulness        0.92
answer_relevancy    0.86
context_precision   0.90
context_recall      0.67
```

Medido com `apps/api/src/modules/rag/tests/integration/test_ragas_quality_baseline.py`
(opt-in via `RUN_RAGAS_EVAL=1` — chama Gemini de verdade, lento e pago,
nao roda so por infra estar de pe), 12 perguntas sobre as fontes do
NVIDIA Knowledge V2 com conteudo real ingerido (excluindo de proposito
os 3 gaps conhecidos: nvidia-nim-docs e monai-docs por DNS, rapids-docs
por esgotar as estrategias de scraping).

`context_recall` (0.67) e o mais baixo dos 4 — cerca de 1/3 do conteudo
de referencia nao e recuperado pela busca atual. Esse e o numero que
decide a Fase 3: so vale trocar `ts_rank` por BM25/pg_search se uma
mudanca de busca melhorar `context_recall` de forma medida, nao por
suposicao.

Dois bugs reais encontrados e corrigidos durante esta medicao (nenhum
deles e about busca, sao sobre geracao de resposta):
- `apps/api/src/modules/scraping/domain/policies.py`: `link_farm` nao
  estava na lista de problemas que acionam fallback para outra
  estrategia de scraping — paginas de documentacao tecnica com barra de
  navegacao densa (ex. TensorRT-LLM no GitHub Pages) eram rejeitadas na
  primeira estrategia (BS4) sem nunca tentar o Trafilatura, que isola o
  conteudo principal.
- `apps/api/src/modules/rag/infrastructure/llm/langchain_gemini_answer_generator.py`:
  `GeminiRagAnswerResponse.citations` exigia `min_length=1`, forcando o
  Gemini a inventar uma citacao ou falhar a validacao quando a evidencia
  recuperada nao respondia a pergunta. O codigo ainda tinha uma guarda
  redundante que tratava citations vazio como erro de sistema
  (`RagAnswerGenerationError` -> HTTP 502) em vez de resposta valida tipo
  "nao tenho informacao suficiente" — que e exatamente o que o prompt do
  sistema ja pede ("diga isso claramente"). As duas causas levavam
  perguntas legitimamente sem boa evidencia a quebrar `/rag/answer` em
  produção em vez de devolver uma resposta honesta.

## 5. Fase 3 — Busca lexical real (BM25 nativo do Postgres)

So entra se a Fase 2 mostrar que o `ts_rank` atual e de fato um
gargalo de recall. Decisao tecnica ja documentada: nao usar `rank-bm25`
(Python) — exigiria carregar todos os chunks em memoria a cada busca.

Entregaveis:

- avaliar `pg_search` (ParadeDB) como extensao Postgres — troca de
  imagem em `infra/docker-compose.yml` (`postgres:16-alpine` ->
  `paradedb/paradedb` ou instalacao da extensao) e migration para
  indice BM25 em `chunks`;
- nova implementacao de `LexicalSearchRepository`
  (`rag/application/ports.py`) usando o operador de busca BM25 do
  `pg_search`, mantendo o mesmo contrato — `fuse_rankings()` (RRF) e o
  caso de uso `SearchEvidence` nao mudam, so a infraestrutura;
- rodar o mesmo dataset golden da Fase 2 contra a nova implementacao,
  comparar numero antes/depois.

Criterio de pronto:

```txt
metrica do Ragas mostra melhora medida (nao assumida) de recall/
precisao lexical em relacao a Fase 2, com a busca ainda 100% dentro do
Postgres.
```

Dependencias: Fase 2 concluida com numero de baseline.

## 6. Fase 4 — Ajustes finos de reranking e fechamento

Entregaveis:

- extrair modelo do Cohere Rerank para `Settings`
  (`COHERE_RERANK_MODEL`, default `rerank-v3.5`) — **concluido em
  23/06/2026**, `RagFactory.create_reranker()` agora passa
  `settings.cohere_rerank_model`;
- revalidar com Ragas (Fase 2/3) se algum modelo de rerank alternativo
  da Cohere muda a metrica;
- consolidar dashboards do Langfuse (Fase 0) com os numeros de qualidade
  do Ragas (Fase 2/3) em um unico ponto de referencia para decisoes
  futuras.

Criterio de pronto:

```txt
qualquer pessoa do time consegue responder "a busca esta boa?" e
"quanto esta custando?" com numero, sem depender de teste manual.
```

Dependencias: Fases 0, 2 e 3.

## 7. Fase 5 — Fechar o limite arquitetural rag -> embeddings

Encontrado na auditoria de regras arquiteturais de 23/06/2026 (detalhe
completo em `docs/validacao_arquitetural_modulos_workers.md`, secao
"Validacao 23/06/2026"): `rag` e a unica relacao entre modulos deste
projeto que importa classe concreta e excecoes de outro modulo
(`embeddings`) em vez de so o contrato publico
(`embeddings/application/public/embedding_service.py`, que o proprio
docstring declara como "o UNICO arquivo... que outros modulos podem
importar").

Entregaveis:

- `rag/infrastructure/embeddings_adapters/` novo — adapter que depende so
  de `EmbeddingService` (`embeddings/application/public/`), traduzindo
  `EmbeddingServiceUnavailableError`/`EmptyChunkTextError` para uma
  excecao propria de `rag`;
- `rag/application/use_cases/search_evidence.py` passa a depender da
  porta nova, nao de `embeddings.application.use_cases.
  generate_chunk_embedding.GenerateChunkEmbedding`;
- `rag/presentation/routes.py` passa a tratar so excecoes de `rag`, nunca
  `embeddings.domain.exceptions` direto;
- atualizar a linha `rag -> embeddings` em
  `docs/validacao_mensagens_interacoes_modulos.md` (ja marcada com nota de
  nao-conformidade, ver lá) para refletir o contrato correto apos o fix.

Criterio de pronto:

```txt
rag so importa de embeddings.application.public (EmbeddingService e
VectorRepository); nenhum arquivo de rag importa
embeddings.application.use_cases nem embeddings.domain.exceptions direto.
```

Dependencias: nenhuma. Risco baixo — e refatoracao de fronteira, sem mudar
comportamento observavel (`SearchEvidence.search()` continua devolvendo o
mesmo resultado).

### Fase 5 — concluida em 23/06/2026

```txt
rag/application/ports.py            + EmbeddingGenerator (porta nova)
rag/domain/exceptions.py             + RagSearchServiceUnavailableError
rag/infrastructure/embeddings_adapters/embeddings_query_embedder.py (novo)
rag/application/use_cases/search_evidence.py  (usa a porta, nao mais
  GenerateChunkEmbedding de embeddings)
rag/presentation/routes.py           (so excecoes de rag)
rag/factories/rag_factory.py         + create_embedding_generator()
```

Validado: `pytest apps/api/src/modules/rag/tests/
apps/api/src/modules/embeddings/tests/unit/ -q` -> 78 passed, 1 skipped
(integracao que exige Postgres). Grep confirma zero import de
`embeddings.application.use_cases`/`embeddings.domain.exceptions` em
`rag/`. `docs/validacao_mensagens_interacoes_modulos.md` e
`docs/validacao_arquitetural_modulos_workers.md` atualizados para refletir
o contrato real (`EmbeddingService`, nao mais `GenerateChunkEmbedding`).

## 8. Fase 6 — Cache por content_hash/URL (embeddings + scraping)

Dois itens de baixo esforço/alto impacto das seções "Tecnologias
candidatas" de `docs/embeddings/roadmap_embeddings.md` e
`docs/scraping/roadmap_scraping.md`, priorizados pela "Ordem de
implementação recomendada" de `docs/roadmap_produto_final.md` (item 2).

Entregáveis:

- `embeddings`: `EmbeddingJobChunkRepository.find_completed_by_content_hash()`
  (filtra por hash + `model_name`, nunca reusa vetor de modelo diferente)
  + `VectorRepository.get_by_chunk_id()` (recupera vetor existente do
  Qdrant) + `UpsertChunkEmbedding.execute(..., cached_chunk_id=...)` pula a
  chamada ao provider quando há cache hit; `ExecuteEmbeddingJob` consulta o
  cache antes de cada chunk;
- `scraping`: `ScrapingResultRepository.get_recent_by_url(url, since=...)`
  (Postgres + in-memory) + `SCRAPING_RESULT_CACHE_TTL = timedelta(days=3)`
  (`domain/policies.py`); `CreateScrapingJob.execute()` reaproveita um
  resultado aprovado recente sem despachar para a fila.

Critério de pronto:

```txt
2 chunks com texto identico em documentos diferentes geram so 1 chamada ao
provider de embedding; reenviar a mesma URL dentro de 3 dias completa o
job sem raspar de novo.
```

Validado: `pytest apps/api/src/modules/embeddings/tests/
apps/api/src/modules/scraping/tests/unit/ -q` -> todos passam (+7 testes
novos: 3 unit + 1 integração em embeddings, 2 unit + 1 integração em
scraping). Suite completa do projeto: 485 testes coletados, 484 passed +
1 skipped (Ragas opt-in).

Dependências: nenhuma.

## 9. Fora de escopo deste roadmap

```txt
DeepEval em CI — entra quando existir pipeline de CI (P2 do roadmap
geral do produto, docs/roadmap_produto_final.md). Sem CI, DeepEval e so
mais um script manual, sem o valor de regressao automatica.

Integrar Recommendation Agent V11 / Briefing Agent V12 ao caminho
principal — e melhoria de produto (P1 #4/#5 do roadmap geral), nao de
infraestrutura de qualidade. Pode vir depois deste roadmap, usando a
observabilidade da Fase 0 para medir o impacto real do agente vs. o
gerador deterministico V1.

Autenticacao, CORS, rate limiting, deploy — P2 de producao, fora do
escopo de "qualidade do pipeline existente".
```

## 10. Ordem resumida

```txt
Fase 0 (observabilidade)  ----\
                                >--- podem comecar em paralelo
Fase 1 (fix recommendations) --/

Fase 2 (baseline Ragas) -> Fase 3 (BM25, so se Fase 2 justificar)
                          -> Fase 4 (fechamento e dashboards)

Fase 5 (fix arquitetural rag->embeddings) -- independente, pode rodar em
                                              paralelo com qualquer fase

Fase 6 (cache embeddings + scraping) -- independente, concluida em
                                          23/06/2026
```

Para a ordem de implementacao que cruza isto com os itens de produto (P1
do `docs/roadmap_produto_final.md`) e as secoes "Tecnologias candidatas"
de cada modulo, ver `docs/roadmap_produto_final.md`, secao "Ordem de
implementacao recomendada" — este documento aqui cobre so qualidade do
pipeline existente, nao features novas de produto.

## 11. Referencias

```txt
docs/diagnostico_fraquezas_e_tecnologias_recomendadas.md  — diagnostico completo
docs/rag/rag_v3_busca_hibrida.md                          — decisao Postgres FTS vs BM25
docs/rag/rag_v4_reranking.md                              — Cohere Rerank atual
docs/rag/roadmap_rag.md                                   — RAG V5 (avaliacao)
docs/recommendations/roadmap_recommendations.md
docs/validacao_arquitetural_modulos_workers.md            — violacao rag->embeddings (Fase 5)
docs/embeddings/roadmap_embeddings.md                     — cache por content_hash (Fase 6)
docs/scraping/roadmap_scraping.md                         — cache por URL (Fase 6)
docs/roadmap_produto_final.md                             — Ordem de implementacao recomendada
apps/api/src/modules/recommendations/domain/policies.py
apps/api/src/modules/rag/infrastructure/database/postgres_lexical_search_repository.py
apps/api/src/modules/rag/application/ports.py
apps/api/src/modules/rag/application/use_cases/search_evidence.py
apps/api/src/modules/embeddings/application/use_cases/execute_embedding_job.py
apps/api/src/modules/scraping/application/use_cases/create_scraping_job.py
```
