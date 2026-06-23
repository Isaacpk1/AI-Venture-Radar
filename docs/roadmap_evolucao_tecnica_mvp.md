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
  (`COHERE_RERANK_MODEL`, default `rerank-v3.5`) — pendencia trivial ja
  documentada;
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

## 7. Fora de escopo deste roadmap

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

## 8. Ordem resumida

```txt
Fase 0 (observabilidade)  ----\
                                >--- podem comecar em paralelo
Fase 1 (fix recommendations) --/

Fase 2 (baseline Ragas) -> Fase 3 (BM25, so se Fase 2 justificar)
                          -> Fase 4 (fechamento e dashboards)
```

## 9. Referencias

```txt
docs/diagnostico_fraquezas_e_tecnologias_recomendadas.md  — diagnostico completo
docs/rag/rag_v3_busca_hibrida.md                          — decisao Postgres FTS vs BM25
docs/rag/rag_v4_reranking.md                              — Cohere Rerank atual
docs/rag/roadmap_rag.md                                   — RAG V5 (avaliacao)
docs/recommendations/roadmap_recommendations.md
apps/api/src/modules/recommendations/domain/policies.py
apps/api/src/modules/rag/infrastructure/database/postgres_lexical_search_repository.py
apps/api/src/modules/rag/application/ports.py
```
