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

Nao existe worker para `recommendations`, `briefing`, `nvidia_knowledge` ou
`orchestration` V1 porque as operacoes atuais sao sincronas e pequenas.

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
```

Factories podem compor dependencias concretas entre modulos; application/domain
nao devem importar detalhes internos de outro modulo.

---

## Pontos De Atencao

```txt
NVIDIA Knowledge V2 precisa decidir escopo de RAG para conteudo NVIDIA
Orchestration V2 precisa juntar fluxo desde URL bruta
Agents V10-V12 devem usar contratos publicos como tools
```

---

## Testes

Estado registrado:

```txt
377 passed
13 integration failures por falta de infra local
```

Antes de qualquer release, rodar integracao com Postgres/Redis/Qdrant ativos.
