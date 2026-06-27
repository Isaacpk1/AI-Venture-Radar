# Roadmap do Modulo Orchestration

O modulo `orchestration` encadeia os modulos de conteudo em um unico
endpoint, registrando o resultado agregado de cada execucao como um
`AnalysisJob`.

Ele nao faz scraping, nao gera embeddings e nao decide regras de negocio de
nenhum outro modulo. Ele so chama, na ordem certa, o que outros modulos ja
expoem publicamente.

---

## Objetivo do Modulo

```txt
startup_id -> dispara recommendations -> dispara briefing -> AnalysisJob
```

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| Orchestration V1 | Implementado | analysis_jobs a partir de startup_id existente |
| Orchestration V2 | Implementado | Entrada por URL bruta, ponta a ponta ate o briefing |
| Orchestration V2.1 | Implementado | Primeira rodada automatica de enriquecimento por URLs do mesmo dominio |
| Orchestration V3 | Futuro | Retomada de jobs falhados (retry por etapa) |
| Orchestration V4 | Futuro | Notificacoes de conclusao |

O detalhamento da prioridade de produto esta em `docs/roadmap_produto_final.md`.

---

## Orchestration V1 - analysis_jobs a partir de startup_id

Status:

```txt
implementado
```

Decisao de escopo (confirmada com o usuario, ver
`docs/orchestration/orchestration_v1_analysis_jobs.md`):

```txt
V1 assume que scraping, ingestion, embeddings e evidencias da startup ja
foram feitos manualmente. Entrada e um startup_id existente, nao uma URL
bruta - isso evitaria reabrir o design das tres pipelines assincronas que
ja existem (scraping/ingestion/embeddings) so para fazer polling de status.
```

Entregaveis:

- entidade `AnalysisJob` com ciclo de vida `pending -> running ->
  completed|failed`;
- contratos publicos novos em `recommendations`
  (`RecommendationGenerator`) e `briefing` (`BriefingGenerator`) para
  disparar geracao via chamada cross-modulo;
- `ExecuteAnalysisJob` — encadeia `RecommendationGenerator.generate()` e
  `BriefingGenerator.generate()`, registra sucesso/falha;
- `POST /analysis/jobs`, `GET /analysis/jobs/{id}`,
  `GET /analysis/jobs?startup_id=`;
- testes unitarios das transicoes e do caso de uso, teste de persistencia
  PostgreSQL.

Criterio de pronto:

```txt
uma startup com evidencias e perfil ja coletados recebe, com uma unica
chamada, recomendacoes geradas e um briefing executivo, com o resultado
agregado rastreavel em analysis_jobs
```

Documento da entrega: `docs/orchestration/orchestration_v1_analysis_jobs.md`.

---

## Orchestration V2 - Entrada por URL Bruta

Status:

```txt
implementado
```

Entregaveis:

- criar/disparar `scraping_job` a partir da URL - entregue;
- persistir `url_ingestion_jobs` com `source_type` - entregue;
- avançar scraping -> ingestion -> embeddings por chamada explicita - entregue;
- worker/dispatcher para reenfileirar advance ate estado terminal - entregue;
- criar ou associar a `Startup` correspondente - entregue;
- disparar extract e classify - entregue (best-effort, nao bloqueia o
  restante quando o servico de LLM nao esta configurado);
- disparar recommendations e briefing - entregue;
- expor resultado agregado (`startup_id`/`recommendation_count`/
  `briefing_id`) adequado ao polling do frontend - entregue.

**Criterio de conclusao:** uma URL submetida deve chegar a um briefing sem
intervencao manual, preservando IDs, estados e erros de cada etapa para consulta
e retomada. Atingido.

Documentos da entrega: `docs/orchestration/orchestration_v2_url_ingestion_jobs.md`,
`docs/orchestration/orchestration_v2_worker_automatico.md` e
`docs/orchestration/orchestration_v2_jornada_completa.md` (fechamento final).

**Extensao feita em 24/06/2026 (continua V2 — historico global de jobs
para o Frontend V3, ver `docs/frontend/roadmap_frontend.md` bloco 2):**
`UrlIngestionJobRepository` so tinha `save`/`get_by_id`; ganhou
`list_page()` (mirror exato do `list_page` que `startups` ja tinha feito
na Startups V3) + `ListUrlIngestionJobs` (use case) +
`GET /url-ingestion/jobs` paginado com filtros `status`/`source_type`.
Consumido pela pagina `/jobs` do frontend. Testes: 28 unit/2 integracao
-> 29 unit/3 integracao.

**Extensao feita em 25/06/2026 (continua V2 — limpeza de vetores orfaos
no Qdrant):** o item de backlog "sincronia Qdrant<->Postgres" supunha
edicao de `Document`/`ScrapingResult`, que nao existe no codigo
(write-once) — investigado antes de implementar algo sem chamador real
(regra 8 do `CLAUDE.md`). Gatilho real confirmado: re-scrape da mesma
URL apos `SCRAPING_RESULT_CACHE_TTL` (3 dias, modulo `scraping`) expirar
cria um `Document` novo; o antigo (e seus vetores no Qdrant) ficava
orfao pra sempre. `UrlIngestionJobRepository.list_completed_by_url(url)`
(novo) acha jobs concluidos anteriores da mesma URL;
`EmbeddingsPort.delete_vectors_for_document()` (novo, delega pra
`VectorRepository.delete_by_document_id()` do modulo `embeddings`, ver
`docs/embeddings/roadmap_embeddings.md`)
chamado por `AdvanceUrlIngestionJob._cleanup_superseded_vectors()` logo
que o embedding e' confirmado concluido — best-effort, falha so gera
`logger.warning`, nao impede o job atual de terminar. Testes: 29 unit/3
integracao -> 31 unit/4 integracao. Validado contra Postgres e Qdrant
reais via script manual, alem de unit/integration tests com fakes/colecao
descartavel.

**Extensao feita em 26/06/2026 (continua V2 - primeira fatia de
enriquecimento automatico):** depois de `try_extract`/`try_classify` na etapa
`ANALYZING`, `AdvanceUrlIngestionJob` consulta o perfil consolidado da
startup. Se `founders`, `funding_stage` ou `customers` ainda estiverem vazios,
e o job estiver em `enrichment_round < 1`, a orquestracao cria ate 2
`url_ingestion_jobs` filhos para o mesmo `startup_id`, usando paginas
candidatas do mesmo dominio (`/about`, `/team`, `/customers`,
`/case-studies`). A tabela `url_ingestion_jobs` ganhou `parent_job_id` e
`enrichment_round`; o repositorio ganhou `list_by_startup_id()` para dedupe
por URL ja conhecida; e os jobs filhos sao despachados pela mesma fila
`url_ingestion`. Testes unitarios de orquestracao: 34 passed.

**Extensao feita em 26/06/2026 (continua V2 - busca externa opcional):** o
modulo `agents` ganhou `SearchExecutorPort` e o adapter HTTP
`TavilySearchExecutor`, configurado por `TAVILY_API_KEY`/
`TAVILY_SEARCH_URL`. `AdvanceUrlIngestionJob` agora tenta usar Search Planner
+ executor de busca para encontrar URLs externas antes do fallback do mesmo
dominio. Sem chave Tavily, a factory devolve `None` e o fluxo segue usando as
paginas do dominio inicial. Testes focados: 22 passed.

**Extensao feita em 26/06/2026 (continua V2 - resgate de fonte fraca):**
quando o scraping de uma fonte `startup_evidence` falha porque o conteudo foi
rejeitado pela validacao ou pede mais fontes, a orquestracao cria uma startup
minima pelo dominio e agenda jobs filhos de enriquecimento. O job original
continua `failed` para auditoria, mas a descoberta nao morre ali. Conteudo
fraco nao vira evidencia aceita; ele so serve para disparar busca por fontes
melhores. Teste focado: rejeicao de `https://www.kunumi.com/` agenda URLs
externas/mesmo dominio como jobs filhos.

---

## Orchestration V3 - Retomada de Jobs Falhados

Entregaveis:

- identificar em qual etapa um `AnalysisJob` falhou;
- permitir retomar so a partir da etapa que falhou, sem refazer o que ja
  funcionou.

---

## Orchestration V4 - Notificacoes

Entregaveis:

- notificar quando um `AnalysisJob` terminar (webhook ou e-mail);
- relatorio de execucoes em lote.

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

Confirmado em `application/use_cases/advance_url_ingestion_job.py`: a etapa
`ANALYZING` roda create/associate `Startup` -> attach evidence ->
try_extract/try_classify -> recommendations -> briefing numa unica
entrega; se falhar no meio, o job inteiro vai para `failed` (terminal, sem
retry granular) mesmo que os primeiros passos tenham funcionado.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| `ANALYZING` falha por completo mesmo quando so o ultimo sub-passo (ex: briefing) deu erro | mais campos de progresso na propria tabela `url_ingestion_jobs` (ja existe `startup_id`/`evidence_attached`/`recommendation_count`/`briefing_id` como guardas de idempotencia parcial) — registrar explicitamente qual sub-passo falhou para o retry pular os ja concluidos | Orchestration V3 (Retomada de jobs falhados) | Medio — migration pequena + logica em `advance_url_ingestion_job.py`, sem infra nova |
| Frontend so descobre conclusao via polling (`GET /url-ingestion/jobs/{id}` a cada 3s) | nenhuma tecnologia nova necessaria agora: webhook simples (POST de callback) resolve o caso de uso da V4 sem precisar de WebSocket/SSE, ja que o consumidor e' o proprio backend do frontend (BFF), nao o navegador direto | Orchestration V4 (Notificacoes) | Baixo |

Nao adotar uma fila de eventos nova (Kafka, RabbitMQ, Redis Streams) para
notificar etapas: o projeto ja usa Dramatiq+Redis para todo o assincrono, e
a propria fila `url_ingestion` ja funciona como o loop de polling
(`UrlIngestionStillProcessingError` + reentrega). Adicionar um barramento de
eventos resolveria um problema de latencia que ainda nao foi medido como
real, e contradiria a regra 8 do `CLAUDE.md` ("construir so o que e
necessario agora").

### Chain de enriquecimento por busca

Pergunta original: depois de raspar uma URL e extrair o perfil da startup,
campos como `founders` muitas vezes ficam vazios porque a pagina raspada
nunca mencionou isso. Hoje `AdvanceUrlIngestionJob` roda `try_extract` uma
unica vez e para — se o campo nao estava na evidencia, fica vazio para
sempre, sem nova tentativa.

Status em 26/06/2026: a chain ja detecta perfil incompleto, limita a uma
rodada, cria jobs filhos e, quando `GEMINI_API_KEY` + `TAVILY_API_KEY` estao
configuradas, tenta fontes externas planejadas pelo Search Planner antes de
cair no fallback do mesmo dominio. Tambem cobre o caso em que a URL inicial
e' fraca demais e falha ainda no scraping: a fonte e marcada como falha, mas
dispara enriquecimento para a startup minima.

O que ainda falta: validar com Tavily real, calibrar ranking/allowlist de
dominios confiaveis e decidir se a segunda rodada deve existir alem do limite
inicial `MAX_ENRICHMENT_ROUNDS = 1`.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| `try_extract` roda uma vez; campo vazio fica vazio para sempre | checagem de `founders`/`funding_stage`/`customers` vazios e criacao de ate 2 jobs filhos do mesmo dominio | Entregue em 26/06/2026 | Baixo |
| Risco de loop sem fim se a busca nunca achar o dado | `parent_job_id` + `enrichment_round`, com limite inicial `MAX_ENRICHMENT_ROUNDS = 1` | Entregue em 26/06/2026 | Baixo |
| Encontrar fontes fora do dominio original | Search Planner Agent + `SearchExecutorPort` Tavily opcional para achar 1-2 URLs candidatas externas, como LinkedIn, Crunchbase ou paginas de imprensa | Entregue em 26/06/2026; falta validar com chave real | Medio |
| URL inicial fraca falha antes de `ANALYZING` | resgate em `SCRAPING`: cria startup minima e agenda enriquecimento, sem aceitar a fonte fraca como evidencia | Entregue em 26/06/2026 | Baixo |

Custo real desta feature: cada round gasta 1 chamada Gemini (Search
Planner) + 1 chamada de API de busca (Tavily) + 1 scraping completo + 1
nova chamada de extracao (Gemini) — caro o suficiente para so disparar
quando o campo faltante de fato muda o score de uma recomendacao (ex:
`founders`/`funding_stage`, nao qualquer campo). Por isso esta feature
fica depois das fases mais baratas no `docs/roadmap_evolucao_tecnica_mvp.md`
(ver Fase 7).
