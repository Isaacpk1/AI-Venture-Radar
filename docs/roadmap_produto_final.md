# Roadmap para Fechar o Produto

Atualizado em 23/06/2026 a partir da revisao cruzada de codigo, testes e
documentacao. Este documento prioriza o que falta para transformar o backend
atual em um produto utilizavel, operavel e apresentavel.

## Diagnostico resumido

O backend possui scraping, ingestao, embeddings, RAG, catalogo NVIDIA,
startups, recomendacoes, briefings, workers e oito agentes LangGraph. A suite
local passou em 518 testes Python (com 1 skip de integracao) e 13 testes de
frontend (`pytest -q` e `npm test`, 2026-06-23). A
jornada unica da URL ate o briefing (P0 #1) ja esta fechada. O frontend
(P0 #2) **nao falta mais por completo** — Frontend V1 e V2 ja estao
entregues e commitados (`docs/frontend/roadmap_frontend.md`), cobrindo
submissao de URL, acompanhamento de job e o resultado completo da startup
(evidencias, recomendacoes, briefing). O que resta do P0 #2 e'
especificamente historico/listagem paginada (Frontend V3) e revisao
humana/auth (Frontend V5) — ver secao 2 abaixo.

**Decisao de escopo confirmada em 23/06/2026** (ver
`docs/decisoes_pendentes.md`, secao 1): este projeto fica como case/demo,
nao vai pra producao real. Isso fecha a pergunta do P2 abaixo —
autenticacao/CI/CD/backup ficam deliberadamente fora de escopo, nao
"pendente". Tambem fecha a pergunta de auth do Frontend V5: revisao
simples sem login, nao auth completa.

## P0 — Jornada funcional de ponta a ponta

### 1. Fechar Orchestration V2 — ENTREGUE

```txt
entregue
```

Implementado (ver `docs/orchestration/orchestration_v2_jornada_completa.md`):

- criar ou associar uma `Startup` ao concluir a ingestao de uma URL — entregue;
- anexar evidencias rastreaveis ao perfil — entregue;
- executar extract e classify — entregue (best-effort, nao bloqueia o
  restante quando o servico de LLM nao esta configurado);
- gerar recommendations e briefing — entregue;
- persistir o estado, IDs downstream e erro de cada etapa — entregue;
- expor consulta agregada do job para polling do frontend — entregue
  (`startup_id`/`recommendation_count`/`briefing_id` em
  `GET /url-ingestion/jobs/{id}`);
- garantir idempotencia e retomada segura — entregue (guardas contra
  reentrega-por-crash do Dramatiq).

**Pronto quando:** uma URL de startup produz briefing e recomendacoes sem
operacao manual entre as etapas. Atingido.

### 2. Frontend operacional — PARCIALMENTE ENTREGUE (V1+V2)

Arquitetura definida em `docs/frontend/nextjs_arquitetura.md`.
Roadmap versionado em `docs/frontend/roadmap_frontend.md`.

Telas minimas:

- submissao de URL e criacao manual de startup — **entregue (V1)**;
- acompanhamento de pipeline e erros — **entregue (V1)**, pagina
  `/jobs/[jobId]` com timeline e polling;
- evidencias, perfil estruturado e classificacao — **entregue (V2)**,
  pagina `/startups/[startupId]`;
- recomendacoes e briefing com citacoes — **entregue (V2)**;
- listagem paginada de startups — **entregue (Frontend V3, primeira fatia)**:
  `GET /startups` com busca e filtros, pagina `/startups` e cards de
  portfolio; historico global de jobs ainda falta;
- tela de revisao humana e retomada de casos pendentes — **falta
  (Frontend V5)**, depende de autenticacao.

Cobertura inicial entregue: `apps/web` usa Vitest + React Testing Library e
possui 13 testes, incluindo o portfolio de startups. **Correcao em 23/06/2026:** uma
afirmacao anterior de "bug real de Rules of Hooks em `StartupDetails`" nao
se confirmou lendo o arquivo na integra (hooks chamados corretamente,
antes de qualquer `return` condicional) — corrigido aqui e nos outros docs
que repetiam essa afirmacao.

O backend deve receber endpoints de listagem, busca e paginacao consistentes,
incluindo startups e jobs de URL, para suportar a tela de historico (V3).

## P1 — Qualidade da decisao

### 3. Completar NVIDIA Knowledge V2 — ENTREGUE (23/06/2026)

```txt
entregue
```

P0+P1+P2 completo: 20/20 fontes processadas, 17/20 com conteudo
recuperavel via `/rag/search`. Restam 3 gaps sem fix de codigo possivel
agora (DNS intermitente Windows-side em 2 fontes, Firecrawl necessario
para a terceira — ver `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md`,
"Tecnologias candidatas"). Nao bloqueiam mais o restante do P1.

### 4. Recommendations V2/V4

- buscar contexto NVIDIA via RAG com citacoes — **DECIDIDO em 23/06/2026**
  (`docs/decisoes_pendentes.md`, secao 2): vale fazer, fica priorizado
  logo apos o frontend. Caminho tecnico: `recommendations` chama
  `rag/application/public/question_answerer.py`, ja existe, zero tech
  nova. **Entregue:** os adaptadores de recommendations e briefing chamam
  esse contrato com filtro `source_type=nvidia_knowledge` e mantem fallback
  deterministico quando nao houver contexto recuperavel;
- aprofundar o uso de `ai_maturity_level` no score (bonus deterministico inicial entregue);
- adicionar prioridade, confianca, complexidade, proxima acao e trade-offs;
- separar justificativa de negocio da justificativa tecnica;
- integrar Recommendation Agent V11 ao caminho principal — **ENTREGUE em
  23/06/2026**: `orchestration` usa o agente quando `GEMINI_API_KEY` esta
  configurada (justificativa revisada persistida de volta em
  `recommendations`), cai para o gerador V1 puro sem a chave.

### 5. Briefing e revisao

- ligar Qdrant/RAG no briefing tambem — **DECIDIDO em 23/06/2026**, junto
  com o item acima ("ligar o qdrant com o briefing tambem, quero isso
  junto"). Mesmo caminho tecnico, mesmo contrato publico de `rag`. Falta
  implementar;
- integrar Briefing Agent V12 ao fluxo principal — **ENTREGUE em
  23/06/2026**: mesma logica do item acima, prosa reescrita persistida de
  volta em `briefings`;
- exportar HTML/PDF preservando citacoes;
- aprovar/rejeitar, comentar e manter historico de revisao;
- ranquear oportunidades e gerar visao de lote.

## P2 — Prontidao de producao

**FORA DE ESCOPO** (decidido em 23/06/2026 — projeto e' case/demo, ver
"Diagnostico resumido" acima). Lista mantida so como registro do que
ficaria pendente SE este projeto virasse produto real algum dia.

- autenticacao, autorizacao e isolamento por usuario/organizacao;
- CORS configuravel, rate limiting e controles de abuso;
- logs estruturados, correlation IDs, metricas, tracing, alertas e monitoramento
  de custo/latencia de LLM;
- CI com testes, verificacao de migrations e analise estatica;
- Dockerfiles e compose/manifestos para API e todos os workers;
- backups, retencao de dados, limpeza de checkpoints e plano de rollback;
- documentacao de operacao, variaveis de ambiente e runbooks.

## P3 — Apresentacao do case

- escolher e documentar o diferencial: rastreabilidade ponta a ponta, hibrido
  deterministico/agente por excecao e cobertura do NVIDIA Inception sao os
  candidatos mais fortes — **ainda em aberto**, e' a unica pergunta que
  sobrou sem resposta em `docs/decisoes_pendentes.md`;
- preparar demonstracao com uma startup real e fontes NVIDIA recuperaveis;
- definir metricas de valor: tempo ate briefing, cobertura de evidencias,
  qualidade das recomendacoes e taxa de revisao/aprovacao.

## Ordem de implementacao recomendada (atualizado 23/06/2026 apos rodada de decisoes)

Cruza a auditoria de regras arquiteturais
(`docs/validacao_arquitetural_modulos_workers.md`), o roadmap de qualidade
do pipeline (`docs/roadmap_evolucao_tecnica_mvp.md`), as secoes
"Tecnologias candidatas" de cada `docs/<modulo>/roadmap_<modulo>.md` e as
decisoes registradas em `docs/decisoes_pendentes.md`. Nao repete o detalhe
de cada item — so a sequencia e o motivo da ordem.

```txt
JA ENTREGUE (nao repetir):
1. Fix arquitetural rag->embeddings (Fase 5 da evolucao tecnica)
2. Itens triviais (COHERE_RERANK_MODEL, cache por content_hash em
   scraping/ingestion/embeddings)
3. P1 #4/#5 (Recommendation Agent V11 + Briefing Agent V12 no caminho
   sincrono)
```

```txt
PROXIMA SEQUENCIA (tudo abaixo ja tem decisao tomada — falta so
implementar, ver docs/decisoes_pendentes.md):

1. Frontend — Vitest/RTL (sem bug pra corrigir: a afirmacao anterior de
   "bug real de Rules of Hooks" nao se confirmou lendo o codigo, ver
   correcao acima). Primeiro de tudo mesmo assim: e' a unica tela que
   mostra o backend pro "cliente". A base de testes ja foi entregue (13
   testes); ampliar cobertura acompanha os proximos fluxos da V3.

2. BM25/pg_search (Fase 3 da evolucao tecnica) — DECIDIDO fazer
   ("nao gostei desse valor [context_recall 0.67], vale a troca").
   Esforco alto (troca de imagem Postgres, migration, reindexacao) — e'
   o item mais caro desta lista, por isso entra logo, antes de empilhar
   mais coisa em cima de uma busca que ainda nao foi otimizada.

3. RAG real em recommendations + briefing ("ligar o qdrant com o
   briefing tambem") — DECIDIDO fazer, junto. Reusa
   `rag/application/public/question_answerer.py`, zero tech nova. Vem
   depois do BM25 pra já nascer se beneficiando da busca melhor.

4. Protecao de modelo/dimensao no Qdrant + sincronia Qdrant<->Postgres —
   DECIDIDO fazer. Esforco baixo-medio, mas importa fazer antes de
   continuar empilhando uso do Qdrant (itens 2 e 3 acima aumentam a
   dependencia do Qdrant — vale proteger antes de depender mais ainda).

5. rapidfuzz para dedup de startups — DECIDIDO fazer; falta calibrar o
   limiar de similaridade com exemplos reais antes de codar (nao decidir
   um numero no escuro).

6. Frontend V3 completo (cards/listagem, chatbot sobre NVIDIA Knowledge,
   badge de fit, evidencia clicavel, export PDF) — depende parcialmente
   do item 3 (chatbot fica mais forte com RAG ja ligado em
   recommendations/briefing tambem, mesma base de conhecimento).

7. Descoberta de startups com fontes gratuitas (hubs como StartSe,
   Distrito, Endeavor, etc. — ver `docs/scraping/roadmap_scraping.md`,
   "Descoberta de startups") — DECIDIDO fazer pra demo, teto de custo
   zero/gratuito. Isolado dos itens 1-6, pode entrar em paralelo se
   sobrar capacidade, mas nao e' bloqueante pra nenhum deles.

8. Frontend V4 (graficos com Recharts, comparacao, fila em lote) — por
   ultimo entre os itens decididos porque depende de endpoints agregados
   novos no backend (GROUP BY) que nenhum item anterior cria.
```

```txt
FORA DE ESCOPO (decidido, nao revisitar sem motivo novo):
- P2 inteiro (autenticacao, CI/CD, Dockerfiles, backup do Qdrant)
- Redesenho do NVIDIA RAG Agent (V10) pra virar sub-tool de outro agente
```

```txt
AINDA SEM DECISAO:
- P3: qual diferencial apresentar no case (unica pergunta sem resposta em
  docs/decisoes_pendentes.md)
```

---

## Pendencias de documentacao e release

- manter este roadmap como fonte de priorizacao;
- atualizar documentos historicos quando uma entrega alterar seu status;
- versionar e aplicar a migration `7d4f2a9c6e83` antes de deployar o codigo que
  usa `scraping_jobs.source_type`;
- manter o README raiz com o caminho de execucao atualizado.
