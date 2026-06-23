# Validacao Arquitetural - Modulos e Workers

Validacao atualizada em 22/06/2026.

---

## Regra

```txt
API cria/consulta estado
workers recebem somente IDs
modulos concentram regra de negocio
contratos publicos conectam modulos
PostgreSQL/Qdrant guardam estado real
fila nao vira banco
```

---

## Modulos Implementados

```txt
scraping
agents
ingestion
embeddings
startups
rag
nvidia_knowledge
recommendations
briefing
orchestration
```

Todos seguem a estrutura modular esperada:

```txt
domain/
application/
infrastructure/
factories/
presentation/
tests/
```

Excecao intencional: `nvidia_knowledge` V1 nao tem banco nem worker porque e
catalogo estatico em codigo.

---

## Workers

| Worker | Fila | Mensagem |
|---|---|---|
| scraper_worker | scraping | job_id |
| agent_worker | agents | run_id |
| ingestion_worker | ingestion | job_id |
| embedding_worker | embeddings | job_id |
| orchestration_worker | url_ingestion | job_id |

Nao existe worker para `recommendations`, `briefing` ou `nvidia_knowledge`
porque as operacoes atuais sao sincronas e pequenas. `orchestration` ganhou
worker proprio na V2 (`orchestration_worker`, fila `url_ingestion`) — a
linha estava faltando nesta tabela desde a entrega do worker automatico
(ver `docs/orchestration/orchestration_v2_worker_automatico.md`).

---

## Cross-Module Permitido

Padroes confirmados no codigo:

```txt
scraping -> agents/public
embeddings -> ingestion/public
rag -> embeddings/public + ingestion/public
recommendations -> startups/public + nvidia_knowledge/public
briefing -> startups/public + recommendations/public
orchestration -> recommendations/public + briefing/public
startups -> agents/public para extract/classify
nvidia_knowledge -> orchestration/application para criar url_ingestion_jobs
orchestration -> scraping/public + ingestion/public + embeddings/public
```

Factories podem compor dependencias concretas entre modulos; application/domain
nao devem importar detalhes internos de outro modulo.

---

## Pontos De Atencao

```txt
NVIDIA Knowledge V2 ja tem escopo de RAG definido por source_type
Orchestration V2 precisa juntar fluxo desde URL bruta
Agents V10-V12 devem usar contratos publicos como tools
```

---

## Testes

Numero de testes muda a cada entrega — ver a tabela "Test coverage" em
`CLAUDE.md` para a contagem atual verificada (em vez de duplicar um numero
aqui que vai ficar desatualizado de novo).

A suite total pula integracoes dependentes de Postgres/Redis/Qdrant quando os
servicos nao estao disponiveis. Antes de qualquer release, rodar novamente com
a infra ativa para executar esses testes em vez de pula-los.

---

## Validacao 23/06/2026 — violacao real encontrada

Auditoria desta data releu o codigo de todos os 11 modulos contra as regras
acima (e contra o "PRE-DECISION CHECKLIST" do `CLAUDE.md`, que e' a versao
mais detalhada das mesmas regras). Resultado: **1 violacao real e
sistemica**, as outras 9 regras do checklist respeitadas.

### Violacao: `rag` importa internals de `embeddings`, nao so o publico

```txt
apps/api/src/modules/rag/application/use_cases/search_evidence.py:5
  importa embeddings.application.dto.GenerateChunkEmbeddingInput
apps/api/src/modules/rag/application/use_cases/search_evidence.py:9-11
  importa a CLASSE CONCRETA GenerateChunkEmbedding
  (embeddings.application.use_cases.generate_chunk_embedding) e type-hinta
  o construtor de SearchEvidence contra ela, nao contra o ABC publico
  EmbeddingService
apps/api/src/modules/rag/presentation/routes.py:5-8
  importa embeddings.domain.exceptions.EmbeddingServiceUnavailableError/
  EmptyChunkTextError direto na camada de apresentacao (nem e' um adapter
  de infra fazendo traducao - e' a rota HTTP lidando com excecao de
  dominio de outro modulo)
```

`embeddings/application/public/embedding_service.py` diz no proprio
docstring: "este e o UNICO arquivo do modulo embeddings que outros modulos
podem importar". `rag` e a UNICA relacao entre modulos deste projeto sem um
adapter de traducao dedicado — todas as outras (scraping<->agents,
startups<->agents, recommendations<->startups/nvidia_knowledge,
briefing<->startups/recommendations, orchestration<->todos,
agents<->rag/recommendations/briefing) tem um
`infrastructure/*_adapters/` que importa DTO/excecao do outro modulo SO
para traduzir, sempre chamando atraves do ABC publico — `rag` pula essa
peca para `embeddings`.

Nao e' regressao silenciosa: `docs/validacao_mensagens_interacoes_modulos.md`
ja documentava isso desde 22/06/2026 (`GenerateChunkEmbedding` listado como
parte do "contrato" rag->embeddings), so que desalinhado do docstring mais
estrito que `embedding_service.py` ganhou depois. Ver nota datada naquele
documento.

Fix proposto (nao aplicado agora — ver `docs/roadmap_evolucao_tecnica_mvp.md`,
Fase 5): `rag` passa a depender so de
`embeddings.application.public.embedding_service.EmbeddingService` +
`vector_repository.py`; um adapter novo em `rag/infrastructure/
embeddings_adapters/` traduz `EmbeddingServiceUnavailableError`/
`EmptyChunkTextError` para uma excecao propria de `rag`, e
`presentation/routes.py` passa a tratar so excecoes de `rag`.

### Confirmado SEM violacao (calibracao para nao confundir com o padrao acima)

Adapters que importam `application/dto.py`/`domain/exceptions.py` de outro
modulo SO para construir o input ou traduzir a excecao na fronteira, e
chamam tudo atraves do ABC publico do outro modulo (ex:
`scraping/infrastructure/agent_adapters/agents_semantic_investigator.py`,
`agents/infrastructure/recommendations_adapters/recommendation_generator_adapter.py`,
`orchestration/infrastructure/recommendations_adapters/recommendations_adapter.py`)
— isso e' o padrao CORRETO e deliberado deste projeto, documentado
repetidamente no historico de versoes do `CLAUDE.md`. Nao reabrir essa
discussao tratando esses arquivos como violacao.
