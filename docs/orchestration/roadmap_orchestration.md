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
