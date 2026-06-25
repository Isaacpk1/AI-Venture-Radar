# Diagnostico de Fraquezas e Tecnologias Recomendadas

Criado em 23/06/2026. Este documento existe para decisao, nao para execucao
imediata: lista as fraquezas reais do projeto (confirmadas em codigo, nao so
relatadas em outros docs) e avalia quais tecnologias resolvem qual fraqueza,
com esforco e dependencias. Nenhum item aqui foi implementado ainda.

## 1. Metodologia

Tres fontes, nesta ordem de confiabilidade:

```txt
1. Leitura direta de codigo (grep, contagem de arquivos, leitura de policies)
2. Teste manual do fluxo completo (URL -> job -> startup -> recomendacoes -> briefing)
3. Limites ja documentados em docs/*.md (usados so como complemento)
```

A fonte 3 sozinha teria subestimado o problema: varios docs descrevem o
projeto como mais maduro do que o codigo confirma (ver secao 2.1).

## 2. Fraquezas confirmadas

### 2.1 Documentacao desatualizada em relacao ao codigo

```txt
CLAUDE.md descreve shared/ como logger + errors + auth + observability +
queue/. Na pratica shared/ so tem queue/dramatiq_broker.py. Os outros
quatro nunca foram criados.

docs/roadmap_produto_final.md e docs/README.md ainda descrevem o frontend
como "nao iniciado". Na pratica apps/web/ existe com Frontend V1+V2
funcionais (nao commitado ainda no momento deste diagnostico).

docs/recommendations/roadmap_recommendations.md ja foi parcialmente
atualizado (bonus de ai_maturity_level), mas o restante do backlog do
modulo ainda nao reflete os bugs da secao 2.3.
```

Isto importa porque qualquer decisao de tecnologia baseada so em ler os
docs vai superestimar o que existe.

**Atualizacao 23/06/2026 (mesmo dia, depois da execucao das Fases 0-2 de
`docs/roadmap_evolucao_tecnica_mvp.md`):** os dois primeiros itens acima
ja foram resolvidos, registrados aqui so para nao reescrever o diagnostico
original. `apps/web` ja foi commitado (Frontend V1+V2, ver `CLAUDE.md` secao
"Frontend module" e `docs/frontend/roadmap_frontend.md`). `shared/logging/`
e `shared/observability/` ja existem e estao em uso (Fase 0 concluida) —
`shared/` continua sem `errors/`/`auth/`. O restante desta secao (terceiro
item, recommendations) e' tratado na secao 2.3 abaixo, que ja descrevia o
bug real antes do fix.

### 2.2 Observabilidade — a fraqueza mais fundamental

```txt
Busca por "import logging"/"getLogger" em todo apps/api/src/modules/ +
main.py + workers/: um unico arquivo usa logging em todo o projeto —
rag/infrastructure/reranking/cohere_reranker.py. Todo o resto (scraping,
ingestion, embeddings, agents, startups, recommendations, briefing,
orchestration, nvidia_knowledge, todos os workers) nao loga nada.

Isso viola a regra 10 do CLAUDE.md ("every log must include request_id/
job_id/startup_id/...") em praticamente 100% do codigo.

Custo/latencia de LLM: so embeddings registra algo
(estimate_input_tokens), e e estimativa heuristica de tokens de input, nao
uso real reportado pela API, sem custo em $. RAG (geracao de resposta),
Recommendation Agent, Briefing Agent, Startup Classifier, Extraction
Agent — nenhum registra tokens, latencia ou custo de nenhuma chamada
Gemini.

Sem correlation ID propagado entre scraping -> ingestion -> embeddings ->
orchestration -> agents. Debugar uma falha hoje exige ler codigo e
consultar o Postgres na mao (foi o que eu fiz para diagnosticar a secao
2.3).
```

### 2.3 Recommendations — bug confirmado em producao local

Encontrado testando o fluxo real com `https://dadosfera.com.br`: as 5
recomendacoes geradas vieram todas com exatamente 27% de fit.

```txt
Causa 1 — sector/description nunca sao preenchidos no fluxo automatico de
URL. AdvanceUrlIngestionJob usa o clean_text so para nomear a Startup
(startups/application/use_cases/extract_startup_profile.py:73-74 so le e
repassa esses campos, nunca escreve). Toda startup criada via URL fica
sem sinal de perfil estruturado, dependendo 100% do texto bruto raspado.

Causa 2 — match_technologies() (recommendations/domain/policies.py) faz
substring puro, sem word boundary, contra um catalogo em ingles e
conteudo raspado majoritariamente em portugues. Cada tecnologia tem 6
keywords; bateu exatamente 1 por coincidencia linguistica em cada uma:
"agent" em "agentes", "api" em "APIs", "enterprise" no titulo de uma
secao, "throughput" via alias "scale" que e substring de "Escale" (falso
positivo do proprio KEYWORD_ALIASES). 1/6 + bonus de 0.1 (ai_native) =
0.27 em todas — mesma formula, mesma coincidencia, nao e ruido aleatorio.
```

Confirmado via query direta em `startups` (sector=None, description=None
para essa startup) e leitura de `domain/policies.py`.

### 2.4 RAG

```txt
BM25: o projeto ja avaliou e rejeitou rank-bm25 (ver
docs/rag/rag_v3_busca_hibrida.md:27-31) porque a lib exigiria carregar
todos os chunks em memoria Python a cada busca — violaria a regra
"Postgres e fonte de verdade, nao duplicar em memoria". Usa
to_tsvector('simple') + ts_rank nativo do Postgres hoje.

'simple' nao faz stemming — "treinar" e "treinamento" sao termos
diferentes na busca lexical.

Filtro de busca so por source_type, nada por startup/data/categoria.

Modelo do Cohere Rerank fixo em codigo (rerank-v3.5), sem variavel de
ambiente.

Avaliacao: zero hoje. RAG V5 nunca comecou. Nao existe dataset de
perguntas, nao existe metrica de fidelidade/alucinacao, nao existe
regressao automatica de qualidade de busca.
```

### 2.5 Agents — 8 agentes construidos, maioria inacessivel no fluxo real

```txt
So o Evidence Validation Agent (V2) tem human-in-the-loop real.

NVIDIA RAG Agent (V10), Recommendation Agent (V11) e Briefing Agent (V12)
nao tem consumidor sincrono — so acionaveis pela fila generica
agent_runs. O fluxo automatico de producao (AdvanceUrlIngestionJob) usa
so os geradores deterministicos V1 de recommendations/briefing. Os tres
agentes mais "inteligentes" do projeto sao codigo morto no caminho real.

Reclassificacao/reextracao sobrescreve sem historico — nao da pra saber
o que mudou entre duas rodadas.
```

### 2.6 Frontend — construido, sem rede de seguranca

```txt
apps/web possui Frontend V1+V2 e a fundacao de testes: Vitest + React Testing
Library, com 14 testes cobrindo os componentes do MVP e o portfolio. A afirmacao
anterior sobre um bug de Rules of Hooks em `StartupDetails` foi reavaliada e
removida: os hooks sempre estiveram antes dos returns condicionais. Ainda
faltam testes das rotas BFF e dos fluxos futuros de listagem/revisao.
```

### 2.7 Dados de startup e NVIDIA Knowledge (resumo, ja documentado em outros docs)

```txt
Sem dedup multi-fonte (mesma empresa por 2 URLs = 2 Startup diferentes).
sector e texto livre sem taxonomia. funding_amount_usd e escalar unico
em USD, sem rodadas. Sem confianca por campo extraido.

NVIDIA Knowledge V2: so 2/8 fontes P0 validadas ponta a ponta; os 12
lotes P1+P2 nunca foram tentados; hostname intermitente do lado Windows
sem solucao.
```

### 2.8 Producao (transversal)

```txt
Zero autenticacao em qualquer rota HTTP. Sem CORS configuravel. Sem
rate limiting. Sem CI. Sem Dockerfile para API/workers (so a infra de
banco/fila/vetor). Sem backup ou retencao de dados.
```

## 3. Tecnologias avaliadas

### 3.1 Logging estruturado basico — pre-requisito, nao opcional

```txt
Problema que resolve: secao 2.2 inteira.
Estado atual: nao existe (1 arquivo loga em todo o projeto).
```

Antes de qualquer ferramenta de observabilidade externa, precisa existir
algo para ela observar. Sem isso, Langfuse ou qualquer outra ferramenta
so vai capturar as chamadas de LLM que ja passam por LangChain (parte do
sistema), nao o resto do pipeline (scraping, ingestion, embeddings,
orchestration), que e onde a maioria das falhas de produto acontece hoje.

Recomendacao: criar `apps/api/src/shared/logging/` com um logger
estruturado (JSON, correlation IDs conforme a regra 10 do CLAUDE.md) e
instrumentar pelo menos os use cases de cada modulo e os workers.
Esforco: medio, sem dependencia de infra nova.

### 3.2 Langfuse — observabilidade de LLM

```txt
Problema que resolve: parte de 2.2 — visibilidade de custo, latencia,
prompts e respostas de cada chamada Gemini/LangChain (RAG, Extraction,
Startup Classifier, Recommendation Agent, Briefing Agent).
Estado atual: nao usado. Nenhuma chamada de LLM tem tracing hoje.
```

Recomendacao: adotar, mas depois ou junto de 3.1 (Langfuse cobre as
chamadas LLM via LangChain callbacks; nao cobre scraping/ingestion/
embeddings, que nao passam por LangChain). Integra bem porque o projeto
ja usa `langchain_core`/`langchain_google_genai` em todos os pontos de
LLM — o callback handler do Langfuse se pluga direto, sem reescrever
prompts ou grafos.

Esforco: baixo (1 dependencia + variavel de ambiente + callback handler
no client LangChain). Infra nova: precisa de uma instancia Langfuse
(self-hosted via docker-compose, ou cloud).

Dependencia: nenhuma — pode comecar a qualquer momento.

### 3.3 Ragas + DeepEval — avaliacao de RAG

```txt
Problema que resolve: 2.4, item "Avaliacao: zero hoje".
Estado atual: nao existe dataset, nao existe metrica de qualidade.
```

Os dois cobrem necessidades diferentes:

```txt
Ragas — metricas especificas de RAG (faithfulness, context precision/
recall, answer relevancy). Melhor encaixe para validar
SearchEvidence/AnswerQuestion do modulo rag.

DeepEval — mais generico, permite LLM-as-judge customizado e se integra
a CI (pytest). Melhor encaixe para regressao automatica em pipeline.
```

Pre-requisito real antes de qualquer um dos dois: um dataset golden de
perguntas+respostas esperadas. Hoje nao existe. Construir esse dataset
exige ter conteudo NVIDIA Knowledge ingerido o suficiente (hoje so 2/8
fontes P0) — caso contrario a avaliacao mede um corpus pequeno e nao
representativo.

Recomendacao: comecar com Ragas dentro de um teste de integracao do
modulo `rag` (mesmo padrao dos testes de integracao existentes, exige
infra real), so depois de completar mais fontes do NVIDIA Knowledge V2.
DeepEval entra quando houver CI (P2 do roadmap geral), nao antes.

Esforco: medio-alto. Bloqueado por dado (corpus), nao por codigo.

### 3.4 BM25 — recomendacao: nao usar `rank-bm25`, avaliar BM25 nativo do Postgres

```txt
Problema que resolve: 2.4, stemming/recall da busca lexical.
Estado atual: to_tsvector('simple') + ts_rank, decisao documentada e
deliberada contra rank-bm25 (ver docs/rag/rag_v3_busca_hibrida.md:27-31).
```

Reintroduzir `rank-bm25` reabriria exatamente o problema que o time ja
rejeitou (carregar todos os chunks em memoria Python a cada busca).
Se o objetivo e BM25 real (nao so melhorar o `to_tsvector`), a opcao que
preserva "Postgres como fonte de verdade, sem carregar tudo em memoria" e
uma extensao BM25 nativa do Postgres, por exemplo `pg_search` (ParadeDB).
Isso mantem a busca dentro do banco, sem subir um Elasticsearch/OpenSearch
so para isso.

Recomendacao: antes de adotar qualquer BM25, medir se o recall do
`ts_rank` atual e realmente o gargalo (nenhuma metrica disso existe
ainda — depende de 3.3 para medir objetivamente). Sem essa medicao,
trocar a tecnologia e aposta, nao decisao.

Esforco: alto se for extensao Postgres nova (requer rebuild da imagem
`postgres:16-alpine` com a extensao, migration, reindexacao). Bloqueado
por 3.3 (precisa medir antes de trocar).

### 3.5 Cohere Rerank — ja implementado, ajuste pequeno pendente

```txt
Estado atual: RAG V4 ja usa Cohere Rerank (cohere.AsyncClient.rerank()),
com degradacao graciosa sem API key.
Pendencia conhecida: modelo "rerank-v3.5" fixo em codigo, sem variavel
de ambiente.
```

Nao e uma adocao nova — so falta extrair o nome do modelo para
`Settings` (`COHERE_RERANK_MODEL`, default `rerank-v3.5`). Esforco
trivial, sem dependencia.

## 4. Priorizacao (impacto x esforco)

| Item | Impacto | Esforco | Bloqueado por |
|---|---|---|---|
| Logging estruturado basico (3.1) | Alto | Medio | Nada |
| Langfuse (3.2) | Alto | Baixo | Nada (independente de 3.1) |
| Fix bugs de recommendations (secao 2.3) | Alto | Baixo | Nada |
| Cohere model configuravel (3.5) | Baixo | Trivial | Nada |
| Ragas (3.3) | Medio-Alto | Medio | Mais fontes NVIDIA Knowledge ingeridas |
| DeepEval (3.3) | Medio | Medio | CI existir (P2) |
| BM25 / pg_search (3.4) | Incerto | Alto | Medir recall atual com Ragas primeiro |

## 5. Ordem recomendada

```txt
1. Logging estruturado (3.1) + Langfuse (3.2) — em paralelo, sem
   dependencia entre eles nem de infra alem do Langfuse em si
2. Fix dos 2 bugs de recommendations (secao 2.3) — ganho imediato de
   qualidade, zero infra nova
3. Cohere model configuravel (3.5) — trivial, fazer junto do item 2
4. Completar mais fontes do NVIDIA Knowledge V2 — pre-requisito de dado
   para o item 5
5. Ragas dentro dos testes de integracao do modulo rag (3.3)
6. So depois de medir com Ragas: decidir se BM25/pg_search (3.4) vale o
   esforco, com numero em mao em vez de suposicao
7. DeepEval quando CI existir (fora do escopo deste documento)
```

## 6. O que nao fazer agora

```txt
Nao adotar rank-bm25 (Python) — decisao ja tomada e documentada contra,
motivo ainda valido.

Nao comecar Ragas/DeepEval antes de ter dataset golden e mais fontes
NVIDIA Knowledge ingeridas — meriria corpus pequeno, conclusao nao
confiavel.

Nao subir Elasticsearch/OpenSearch so para BM25 — contradiz a regra de
Postgres como fonte de verdade sem necessidade comprovada ainda.
```

## 7. Referencias

```txt
docs/rag/rag_v3_busca_hibrida.md       — decisao Postgres FTS vs BM25
docs/rag/rag_v4_reranking.md           — Cohere Rerank, modelo fixo
docs/rag/roadmap_rag.md                — RAG V5 (avaliacao), ainda futuro
docs/recommendations/roadmap_recommendations.md
docs/agents/agents_v10_nvidia_rag_agent.md
docs/agents/agents_v11_recommendation_agent.md
docs/agents/agents_v12_briefing_agent.md
apps/api/src/modules/recommendations/domain/policies.py
apps/api/src/modules/startups/application/use_cases/extract_startup_profile.py
apps/api/src/modules/rag/infrastructure/reranking/cohere_reranker.py
apps/api/src/modules/embeddings/domain/entities.py
```
