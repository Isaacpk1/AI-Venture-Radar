# Roadmap do Modulo Scraping

O modulo `scraping` coleta conteudo publico da web, valida tecnica e
textualmente, decide entre aceitar/revisar/descartar, e escalona para LLM ou
agente quando a validacao deterministica nao e suficiente.

Ele nao limpa/normaliza texto (isso e `ingestion`) e nao decide se a
evidencia e relevante para uma startup especifica alem do que a validacao
evidencial basica ja cobre.

---

## Objetivo do Modulo

```txt
URL -> estrategia de coleta -> validacao deterministica -> quality_score ->
ACCEPT | LLM_REVIEW | AGENT_REVIEW | FALLBACK | REJECT
```

---

## Estado atual

```txt
V8 - modulo completo (ver CLAUDE.md, secao "Scraping module")
```

Nao ha V9 planejada como feature nova — o modulo cobre hoje toda a
pipeline V1-V8 descrita no `CLAUDE.md` (BS4 -> Playwright -> Trafilatura,
validacao deterministica + semantica + agente, source_type para fontes
curadas). Este documento existe para registrar **tecnologias candidatas**
sobre fraquezas reais encontradas lendo o codigo, nao para inventar uma
nova versao sem necessidade comprovada (regra 8 do `CLAUDE.md`).

Documentos historicos de versao: `docs/scraping/scraper_v1.md` ate
`docs/scraping/scraper_v8_agente_investigacao.md`; visao consolidada em
`docs/scraping/modulo_scraping_atualizado.md`.

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

| Fraqueza confirmada | Tecnologia/abordagem | Impacto | Esforco |
|---|---|---|---|
| Mesma URL raspada de novo sempre refaz o scraping completo (3 estrategias + validacao); `scraping_results.content_hash` ja e unique, mas nada consulta por hash antes de raspar | checagem por `content_hash` (ou pela URL normalizada) antes de iniciar um novo `ScrapingJob` — reusa constraint que ja existe, sem lib nova | Alto (custo de rede + tempo) | Baixo |
| `_has_captcha_challenge()` bloqueia so com base em `< 500 chars` de texto extraido — heuristica de tamanho, nao sinal real de captcha | nenhuma lib nova necessaria: refinar a heuristica com mais de um sinal (ex: presenca de formulario de captcha real no DOM, nao so a palavra "captcha" no JS) | Medio (falsos positivos em paginas legitimas com JS pesado) | Baixo |
| `strategy_selector.py` tenta BS4 -> Playwright -> Trafilatura sequencialmente mesmo quando o padrao de falha (ex: captcha em todas) ja indica que nenhuma vai funcionar | circuit breaker simples por dominio: contar falhas consecutivas do mesmo tipo em Postgres (`scraping_attempts` ja registra cada tentativa) e pular estrategias condenadas sem nova infra | Medio (tempo desperdicado) | Medio |
| Firecrawl e citado em comentarios (`strategy_selector.py`, `scraping_limits.py`, `dto.py`) como fallback pago, mas nunca foi implementado de fato | implementar o client real do Firecrawl (`FIRECRAWL_API_KEY` ja existe em `Settings` desde o inicio do projeto, nunca usada) como ultimo fallback, depois de BS4/Playwright/Trafilatura falharem | Alto para os gaps que ja esgotaram as 3 estrategias atuais (ex: `rapids-docs` no NVIDIA Knowledge V2) | Medio |
| `quality_score` e calculado por tentativa mas nunca persistido como serie — sem visao de distribuicao ao longo do tempo | a infra de logging estruturado (Fase 0 de `docs/roadmap_evolucao_tecnica_mvp.md`) ja existe; falta so logar `quality_score` e a decisao (`ACCEPT`/`LLM_REVIEW`/etc.) em cada tentativa para virar dashboard | Medio (observabilidade) | Baixo — so usar o que `shared/logging` ja entrega |
| `ScrapingLimits.total_timeout_seconds = 90` e fixo, independente do tipo de URL (documentacao tecnica densa timeouta mais que paginas de marketing) | tornar o timeout configuravel por `source_type` (campo que ja existe em `ScrapingJob`), sem lib nova | Baixo-Medio | Baixo |

Nao adotar um servico de scraping totalmente terceirizado (ex: Bright Data,
ScrapingBee) substituindo BS4/Playwright/Trafilatura: as 3 estrategias
atuais cobrem a maioria dos casos reais (ver `nvidia_knowledge_v2_primeira_
validacao_real.md`, 17/20 fontes com conteudo); Firecrawl como ultimo
fallback pago (acima) e suficiente para os poucos casos que esgotam as
estrategias gratuitas, sem trocar a arquitetura inteira do modulo.
