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

### Chain de enriquecimento por busca (discutido em 23/06/2026)

Pergunta original: depois de raspar uma URL e extrair o perfil da startup,
campos como `founders` muitas vezes ficam vazios porque a pagina raspada
nunca mencionou isso. Hoje `AdvanceUrlIngestionJob` roda `try_extract` uma
unica vez e para — se o campo nao estava na evidencia, fica vazio para
sempre, sem nova tentativa.

Confirmado o que falta (ver tambem `docs/agents/roadmap_agentes.md`, secao
do Search Planner Agent): o Search Planner Agent (V3) ja sabe transformar
um objetivo em queries de busca, mas (a) nao tem client de busca real para
virar query em URL, e (b) nunca e chamado automaticamente — so pela fila
generica `agent_runs`.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| `try_extract` roda uma vez; campo vazio fica vazio para sempre | depois de `try_extract` na etapa `ANALYZING`, checar se `founders`/`funding_stage`/`customers` continuam vazios; se sim, chamar o Search Planner Agent + o `SearchExecutorPort` novo (Tavily, ver roadmap de `agents`) para achar 1-2 URLs candidatas (ex: LinkedIn, Crunchbase, pagina `/about`/`/team` do mesmo dominio) | Nova capacidade de orchestration, complementar ao P1 #4 do `docs/roadmap_produto_final.md` | Alto — novo `ScrapingJob` associado ao mesmo `startup_id`, nova chamada de agente, novo round de `try_extract` quando a evidencia chegar |
| Risco de loop sem fim se a busca nunca achar o dado | limite explicito de 1-2 rounds de enriquecimento por `startup_id` (campo novo em `url_ingestion_jobs`, ex: `enrichment_rounds`), mesma disciplina de `max_iterations` que todo agente do projeto ja segue | Mesma feature acima | Baixo (so um contador + guarda) |

Custo real desta feature: cada round gasta 1 chamada Gemini (Search
Planner) + 1 chamada de API de busca (Tavily) + 1 scraping completo + 1
nova chamada de extracao (Gemini) — caro o suficiente para so disparar
quando o campo faltante de fato muda o score de uma recomendacao (ex:
`founders`/`funding_stage`, nao qualquer campo). Por isso esta feature
fica depois das fases mais baratas no `docs/roadmap_evolucao_tecnica_mvp.md`
(ver Fase 7).
