# Roadmap para Fechar o Produto

Atualizado em 26/06/2026 a partir da revisao cruzada de codigo, testes e documentacao.

## Diagnostico resumido

O backend possui scraping, ingestao, embeddings, RAG, catalogo NVIDIA, startups, recomendacoes, briefings, workers, oito agentes LangGraph, orquestracao por URL e descoberta inicial de startups. O frontend operacional existe ate V4.

Decisao de escopo mantida: este projeto e um case/demo. Auth completa, CI/CD, Dockerfiles de producao, backup do Qdrant e operacao real ficam fora de escopo ate haver nova decisao.

## P0 - Jornada funcional de ponta a ponta

### 1. Orchestration V2 - ENTREGUE

```txt
URL -> scraping -> ingestion -> embeddings -> startup/extract/classify
-> recommendations -> briefing
```

Entregue com `url_ingestion_jobs`, worker Dramatiq, polling, IDs downstream, historico paginado e idempotencia contra reentrega.

### 2. Frontend operacional - ENTREGUE ate V4

Entregue:

```txt
/analyze
/jobs
/jobs/[jobId]
/startups
/startups/[startupId]
/knowledge
/dashboard
```

Inclui portfolio, historico global, badge de fit, evidencia clicavel, chatbot NVIDIA Knowledge, export PDF, graficos de portfolio, comparacao de ate 3 startups e fila de analise em lote.

## P1 - Qualidade da decisao

### 3. NVIDIA Knowledge V2 - ENTREGUE

20/20 fontes processadas, 17/20 com conteudo recuperavel. Os 3 gaps restantes nao bloqueiam o MVP: dois sao problema de DNS/ambiente e um exige fallback pago de scraping.

### 4. Recommendations V3 - ENTREGUE

Entregue:

```txt
regras deterministicas
RAG grounding com citacoes NVIDIA
fallback deterministico
confidence
complexity
GET /recommendations/stats
Recommendation Agent V11 no caminho sincrono quando ha GEMINI_API_KEY
```

Ainda futuro: feedback humano e versionamento de geracoes para revisao.

### 5. Briefing V3 - ENTREGUE

Entregue: contexto NVIDIA via RAG, prosa reescrita pelo Briefing Agent V12 quando possivel, Markdown rastreavel e export PDF real.

## P2 - Prontidao de producao

FORA DE ESCOPO do demo:

```txt
auth/autorizacao real
CI/CD
Dockerfiles de deploy
backups e retencao
rate limiting/CORS de producao
alertas e runbooks
```

Fundacoes ja existem: logging estruturado, Langfuse self-hosted no compose e separacao modular de infraestrutura.

## P3 - Apresentacao do case

Diferencial escolhido e implementado: rastreabilidade ponta a ponta. As recomendacoes e citacoes preservam origem em links Markdown clicaveis; o frontend renderiza Markdown em briefing, justificativas e chatbot.

## Frontend V5 - ENTREGUE

Revisao humana simples entregue para recommendations e briefings, com status (`pending`, `approved`, `rejected`), comentario, revisor textual e timestamp. Sem auth completa.

## Startup Discovery - ENTREGUE V1

Descoberta gratuita para demo entregue com tres hubs:

```txt
InovAtiva Brasil
Abstartups
100 Open Startups
```

`POST /startup-discovery/runs` cria uma rodada, persiste `startup_discovery_runs` e submete URLs descobertas para `url_ingestion_jobs` respeitando `STARTUP_DISCOVERY_MAX_PER_RUN`.

## Proxima sequencia recomendada

```txt
1. Validar a chain de enriquecimento com Tavily real e calibrar ranking/allowlist.
2. Expandir Startup Discovery para mais hubs gratuitos alem dos 3 iniciais.
3. Hardening de producao apenas se o projeto deixar de ser demo.
```

## Pendencias de documentacao e release

- Manter `docs/estado_atual_do_projeto.md` como fotografia operacional.
- Atualizar `CLAUDE.md` quando uma entrega mudar migrations, testes ou comandos.
- Evitar reabrir itens ja resolvidos em `docs/decisoes_pendentes.md`.
