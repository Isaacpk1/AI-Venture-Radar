# Módulo Startup Discovery — Visão Geral

## 1. Importância

O `startup_discovery` alimenta o topo do funil: em vez de depender de uma URL
avulsa, descobre startups automaticamente em hubs públicos e as injeta no
pipeline de análise. É o que permite escalar o radar de "uma startup por vez"
para "um lote descoberto sozinho".

## 2. Fluxo

```txt
POST /startup-discovery/runs
  -> cria DiscoveryRun
  -> consulta hubs públicos (InovAtiva Brasil, Abstartups, 100 Open Startups)
  -> extrai URLs (best-effort por hub; falha de um não cancela os outros)
  -> limita por STARTUP_DISCOVERY_MAX_PER_RUN (default 20)
  -> cria url_ingestion_jobs (source_type=startup_evidence)
  -> registra urls_found / jobs_submitted / status
GET /startup-discovery/runs/{id}
```

Run síncrono: fetches de hub são I/O de rede barato (timeout 30s por hub).

## 3. Estrutura de pastas

```txt
startup_discovery/
  presentation/     POST/GET runs
  application/      use_cases (RunStartupDiscovery, GetDiscoveryRun), ports (HubLinkExtractor)
  domain/           DiscoveryRun, hub_registry (HUB_SOURCES), exceções
  infrastructure/   hub_extractors/ (base + 3 concretos), orchestration_adapters/
  factories/
  tests/
```

## 4. Stack

```txt
httpx              fetch dos hubs (30s timeout, follow_redirects)
BeautifulSoup      extração de links/perfis
(reuso) orchestration   submissão como url_ingestion_jobs
```

## 5. Histórico de versões

| Versão | Status | Entrega |
|---|---|---|
| V1 | Entregue | Descoberta em 3 hubs públicos; DiscoveryRun no Postgres; rotas REST |

**Versão atual: V1.** Limitação: seletores CSS estimados (constantes no topo de
cada extrator, fáceis de ajustar). Futuro (mais hubs, agendamento) em
`roadmap.md`.
