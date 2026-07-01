# Roadmap do Modulo Startup Discovery

Criado em 26/06/2026 para documentar o modulo `startup_discovery`, que saiu da secao de ideias do scraping e virou modulo proprio.

---

## Objetivo

```txt
hubs publicos -> extrair URLs de startups -> criar url_ingestion_jobs
```

O modulo nao substitui scraping, ingestion ou orchestration. Ele so descobre URLs candidatas e delega a analise completa para o fluxo ja existente.

---

## Estado Atual - V1 Entregue

Rotas:

```txt
POST /startup-discovery/runs
GET  /startup-discovery/runs/{run_id}
```

Persistencia:

```txt
startup_discovery_runs
```

Migration:

```txt
c9d3e7f0a4b8_create_startup_discovery_runs.py
```

Hubs implementados:

```txt
InovAtiva Brasil
Abstartups
100 Open Startups
```

Configuracao:

```txt
STARTUP_DISCOVERY_MAX_PER_RUN=20
```

Comportamento:

- extratores usam `httpx` + BeautifulSoup;
- links duplicados sao normalizados por URL;
- falha em um hub e best-effort, desde que outros hubs entreguem URLs;
- URLs descobertas sao submetidas ao fluxo de `url_ingestion_jobs` via adapter de orchestration;
- o run registra `hubs_processed`, `urls_found`, `jobs_submitted`, erro e URLs submetidas.

---

## Fora Do Escopo Da V1

```txt
crawler continuo
API paga de busca
Tavily/SearchExecutor
rankeamento sofisticado de hubs
extratores para todos os 14 hubs listados no brainstorm original
```

---

## Proximas Evolucoes

1. Expandir gradualmente para mais hubs gratuitos.
2. Persistir ou relatar URLs descartadas por duplicidade/erro.
3. Adicionar filtros simples por hub quando a lista crescer.
4. Integrar com a chain de enriquecimento por busca quando uma startup conhecida precisar de fontes melhores.
5. Rodar discovery recorrente por cron/scheduler com guardrails e metricas.

Documento de desenho: `docs/startup_discovery/cron_discovery_hubs.md`.
