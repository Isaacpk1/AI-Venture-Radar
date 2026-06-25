# Roadmap para Fechar o Produto

Atualizado em 23/06/2026 a partir da revisao cruzada de codigo, testes e
documentacao. Este documento prioriza o que falta para transformar o backend
atual em um produto utilizavel, operavel e apresentavel.

## Diagnostico resumido

O backend possui scraping, ingestao, embeddings, RAG, catalogo NVIDIA,
startups, recomendacoes, briefings, workers e oito agentes LangGraph. A suite
local passou em 524 testes Python (com 1 skip opt-in, Ragas) e 23 testes de
frontend (`pytest -q` e `npm test`, reconferido em 2026-06-24 apos o
fechamento do Frontend V3). A
jornada unica da URL ate o briefing (P0 #1) ja esta fechada. O frontend
(P0 #2) **esta completo** — Frontend V1, V2 e V3 ja estao
entregues e commitados (`docs/frontend/roadmap_frontend.md`), cobrindo
submissao de URL, acompanhamento de job, resultado completo da startup
(evidencias, recomendacoes, briefing), portfolio paginado, historico
global de jobs, badge de fit, evidencia clicavel, chatbot sobre NVIDIA
Knowledge e export do briefing em PDF. O que resta do P0 #2 e'
so revisao humana/auth (Frontend V5, deliberadamente sem auth completa)
— ver secao 2 abaixo.

**Decisao de escopo confirmada em 23/06/2026** (`docs/decisoes_pendentes.md`
foi reorganizado depois disso — ver a tabela "Decisoes ja resolvidas" la,
linha "Projeto e' demo ou produto real?"): este projeto fica como
case/demo, nao vai pra producao real. Isso fecha a pergunta do P2 abaixo —
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

### 2. Frontend operacional — ENTREGUE (V1+V2+V3)

Arquitetura definida em `docs/frontend/nextjs_arquitetura.md`.
Roadmap versionado em `docs/frontend/roadmap_frontend.md`.

Telas minimas:

- submissao de URL e criacao manual de startup — **entregue (V1)**;
- acompanhamento de pipeline e erros — **entregue (V1)**, pagina
  `/jobs/[jobId]` com timeline e polling;
- evidencias, perfil estruturado e classificacao — **entregue (V2)**,
  pagina `/startups/[startupId]`;
- recomendacoes e briefing com citacoes — **entregue (V2)**;
- listagem paginada de startups — **entregue (Frontend V3)**:
  `GET /startups` com busca e filtros, pagina `/startups` e cards de
  portfolio;
- historico global de jobs — **entregue (Frontend V3, 24/06/2026)**:
  `GET /url-ingestion/jobs` paginado + pagina `/jobs`;
- badge de fit, evidencia clicavel por recomendacao, chatbot sobre NVIDIA
  Knowledge e export do briefing em PDF — **entregue (Frontend V3,
  24/06/2026)**, ver `docs/frontend/roadmap_frontend.md` blocos 3-5;
- tela de revisao humana e retomada de casos pendentes — **falta
  (Frontend V5)**, depende de autenticacao.

Cobertura: `apps/web` usa Vitest + React Testing Library e possui 23
testes (reconferido 24/06/2026, +9 do fechamento do Frontend V3).
**Correcao em 23/06/2026:** uma
afirmacao anterior de "bug real de Rules of Hooks em `StartupDetails`" nao
se confirmou lendo o arquivo na integra (hooks chamados corretamente,
antes de qualquer `return` condicional) — corrigido aqui e nos outros docs
que repetiam essa afirmacao.

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
  junto"). Mesmo caminho tecnico, mesmo contrato publico de `rag`.
  **Entregue em 24/06/2026:** `NvidiaContextGrounder` +
  `RagNvidiaContextGrounder` geram a secao "Contexto NVIDIA" no Markdown
  do briefing, com fallback deterministico sem `GEMINI_API_KEY`/sem
  citacao real (ver `docs/briefing/roadmap_briefing.md`);
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

**Diferencial escolhido (24/06/2026): rastreabilidade ponta a ponta** —
toda recomendacao e citacao tem origem rastreavel, do URL bruto ate o
briefing final. Os outros 2 candidatos (hibrido deterministico/agente por
excecao, cobertura do NVIDIA Inception) ficam como apoio na narrativa, nao
como o eixo principal da demo. Decisao registrada em
`docs/decisoes_pendentes.md` (tabela "Decisoes ja resolvidas").

O que essa escolha exigiu (gaps reais encontrados ao revisar o que ja
existia, fechados em 24/06/2026):
- evidencia clicavel por recomendacao e badge de fit — ja entregues no
  fechamento do Frontend V3 (ver `docs/frontend/roadmap_frontend.md`);
- citacoes NVIDIA (recommendations/briefing, RAG grounding) viravam texto
  puro (`Fontes: url1, url2`) em vez de link Markdown — corrigido em
  `generate_recommendations.py`/`generate_briefing.py`;
- o briefing era renderizado como texto cru (`<pre>`) na tela da startup
  — nenhum link (nem os de evidencia, que ja eram Markdown valido desde a
  V1) ficava clicavel fora do PDF exportado. Corrigido com renderizacao
  real de Markdown no frontend (`react-markdown`), reaplicada tambem na
  justificativa de cada recomendacao e na resposta do chatbot.

Ainda nesta secao, sem decisao de prioridade vs. o resto do backlog:
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
4. BM25/pg_search (Fase 3 da evolucao tecnica) — troca de imagem Postgres
   (`paradedb/paradedb`), migration `b3f6e91c7d45`, ver
   `docs/rag/roadmap_rag.md`
5. RAG real em recommendations + briefing — `NvidiaKnowledgeGrounder`
   (recommendations, 24/06/2026) + `NvidiaContextGrounder` (briefing,
   24/06/2026), fallback deterministico nos dois sem `GEMINI_API_KEY`
6. Protecao de modelo/dimensao no Qdrant — `EmbeddingCollectionSchemaMismatchError`,
   recusa upsert com schema incompativel (24/06/2026)
7. Frontend V3, primeira fatia — `GET /startups` paginado + pagina
   `/startups` (24/06/2026)
8. Frontend V3, resto completo — historico global de jobs
   (`GET /url-ingestion/jobs` paginado + pagina `/jobs`), badge de fit +
   evidencia clicavel em `startup-details.tsx`, chatbot sobre NVIDIA
   Knowledge (`/knowledge`, so UI sobre `/rag/answer` ja existente),
   export do briefing em PDF (24/06/2026 — ver decisao tecnica abaixo)
```

```txt
DECISAO TECNICA REGISTRADA (24/06/2026, dentro do item 8 acima):
export do briefing trocou `weasyprint` (planejado originalmente) por
Playwright + Jinja2 + `markdown`. `weasyprint` exige bibliotecas nativas
(Pango/Cairo/GTK) com risco real de instalacao no Windows (ambiente
deste projeto); `playwright` ja e' dependencia do projeto desde o
Scraping V4 e ja funciona comprovadamente aqui. Ver
docs/briefing/briefing_v3_export_pdf.md.
```

```txt
PROXIMA SEQUENCIA (atualizado 24/06/2026 apos o fechamento do Frontend
V3 — tudo abaixo ja tem decisao tomada, ver docs/decisoes_pendentes.md,
sem ordem de prioridade definida entre os itens 1-3):

1. Sincronia Qdrant<->Postgres (reupsert do payload do Qdrant quando
   `Document`/`ScrapingResult` mudar) — DECIDIDO fazer, ainda nao
   implementado; risco pratico baixo hoje porque nao existe fluxo de
   edicao de evidencia ainda, protecao preventiva.

2. rapidfuzz para dedup de startups — DECIDIDO fazer; falta calibrar o
   limiar de similaridade com exemplos reais antes de codar (nao decidir
   um numero no escuro).

3. Descoberta de startups com fontes gratuitas (hubs como StartSe,
   Distrito, Endeavor, etc. — ver `docs/scraping/roadmap_scraping.md`,
   "Descoberta de startups") — DECIDIDO fazer pra demo, teto de custo
   zero/gratuito. Isolado dos itens 1-2, pode entrar em paralelo se
   sobrar capacidade.

4. Frontend V4 (graficos com Recharts, comparacao, fila em lote) — por
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
- atualizar documentos historicos quando uma entrega alterar seu status
  (auditoria mais recente: 24/06/2026, ver `CLAUDE.md` "Authoritative
  Current State");
- manter o README raiz com o caminho de execucao atualizado.

Item resolvido (removido desta lista em 24/06/2026): a migration
`7d4f2a9c6e83` ja esta aplicada — `alembic current` confirma head em
`b3f6e91c7d45`, que vem depois dela na cadeia.
