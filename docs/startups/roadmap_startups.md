# Roadmap do Modulo Startups

O modulo `startups` representa empresas, evidencias associadas e dados
estruturados usados para classificacao e recomendacao.

Ele nao faz scraping, nao gera embeddings e nao recomenda tecnologias sozinho.
Ele organiza a base relacional das startups.

---

## Objetivo do Modulo

```txt
consolidar varias evidencias em uma representacao estruturada de startup
```

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| Startups V1 | Implementado | Modelo relacional basico |
| Startups V2 | Implementado (slice inicial) | Campos estruturados (founders/funding/customers) |
| Startups V3 | Implementado (slice inicial) | Classificacao de maturidade em IA |
| Startups V4 | Futuro | Auditoria e confianca |

---

## Startups V1 - Modelo Relacional Basico

Entregaveis:

- entidade `Startup`;
- entidade `StartupEvidence`;
- migration para `startups` e `startup_evidences`;
- repositorios PostgreSQL;
- casos de uso para criar, buscar e atualizar startup;
- testes de persistencia.

Criterio de pronto:

```txt
o sistema consegue cadastrar uma startup e associar evidencias aprovadas
```

Entregue:

- entidades `Startup` e `StartupEvidence`;
- migration `startups` e `startup_evidences`;
- repositorios PostgreSQL;
- casos de uso para criar, buscar e atualizar startup;
- caso de uso para associar e listar evidencias;
- rotas HTTP basicas em `/startups`;
- `GET /startups` paginado, com busca textual e filtros por setor, pais e
  maturidade de IA, para o portfolio do Frontend V3;
- testes unitarios e teste de persistencia PostgreSQL.

Documento da entrega: `docs/startups/startups_v1_modelo_relacional.md`.

---

## Startups V2 - Campos Estruturados (slice inicial)

Status:

```txt
implementado (slice inicial — so os campos estruturados; deduplicacao e
consolidacao multi-fonte ficaram fora, ver limites abaixo)
```

O brief original do case (secao 2) pede coleta de "empresa, produto,
setor, **clientes**, **funding**, **founders** e tecnologias utilizadas".
O `Startup` da V1 so tinha `name`, `website_url`, `description`,
`sector`, `country` — nenhum campo estruturado para founders, funding ou
clientes. Essa informacao, se coletada, ficava perdida em texto livre
(ver `docs/diagnostico_case_original_e_novas_prioridades.md`, secao 6).

Entregue:

- enum `FundingStage` (`PRE_SEED/SEED/SERIES_A/SERIES_B/SERIES_C_PLUS/UNKNOWN`);
- campos novos em `Startup`: `founders: tuple[str, ...]`, `funding_stage`,
  `funding_amount_usd`, `customers: tuple[str, ...]`;
- `Startup.update()` estendido para aceitar os 4 campos novos;
- migration `f77998c46d08` (`ALTER TABLE startups`, 4 colunas — JSONB
  para as listas, NOT NULL com default `[]`);
- `PATCH /startups/{id}` aceita os campos novos.

Esses campos sao o destino natural do futuro `Extraction Agent`
(`agents` V8), agora desbloqueado.

Fora do escopo desta entrega (registrado como limite conhecido):
deduplicar startups por nome/site, associar multiplas fontes a mesma
startup, registrar origem de cada campo, confianca por evidencia — isso
continua pendente para uma V2.5/V4 futura se houver necessidade real.

Documento da entrega: `docs/startups/startups_v2_campos_estruturados.md`.

---

## Startups V3 - Classificacao de Maturidade em IA

Status:

```txt
implementado (slice inicial — ver "escopo desta entrega" no documento da
entrega)
```

Esta versao e a contraparte, do lado de dados, do `Startup Classifier
Agent` (`agents` V9). Fechou a lacuna identificada como mais critica do
projeto em `docs/diagnostico_case_original_e_novas_prioridades.md` secao
3: `recommendations` gerava recomendacoes sem nenhuma classificacao
previa da startup.

Entregue:

- enum `AiMaturityLevel` (`AI_NATIVE` / `AI_ENABLED` / `NON_AI`);
- 3 colunas novas em `startups` (`ai_maturity_level`,
  `classification_reason`, `classified_at`) via `ALTER TABLE`, nao
  entidade separada — classificacao e atributo 1:1 do `Startup`;
- `Startup.classify(level, reason)` (metodo de dominio);
- `StartupClassifierPort` (`application/ports.py`) + adapter
  (`infrastructure/agent_adapters/agents_startup_classifier.py`) chamando
  `agents` sincronamente;
- `POST /startups/{id}/classify`;
- testes unitarios e de persistencia PostgreSQL.

Fora do escopo desta entrega (registrado como limite conhecido):
"classificar tipo de uso de IA" e "estimar maturidade tecnica" como
dimensoes distintas (a classificacao em 3 niveis cobre ambas de forma
simplificada); `recommendations` ainda nao consulta
`Startup.ai_maturity_level`; sem historico de classificacoes
(reclassificar sobrescreve).

Documento da entrega: `docs/startups/startups_v3_classificacao_maturidade.md`.

---

## Startups V4 - Auditoria e Confianca

Entregaveis:

- historico de alteracoes;
- score de confianca por campo;
- trilha de evidencias;
- suporte a revisao humana futura.

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

Confirmado em `application/use_cases/create_startup.py`: nao existe nenhuma
checagem de duplicidade antes de criar um `Startup` novo. Duas URLs
diferentes sobre a mesma empresa (ex: site institucional + pagina de
imprensa) criam dois registros `Startup` distintos, cada um com seu proprio
conjunto parcial de evidencias/recomendacoes/briefing.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| Sem dedup multi-fonte — mesma empresa por 2 URLs = 2 `Startup` | `rapidfuzz` (lib pequena, sem infra nova) para comparar `name`/`website_url` contra startups existentes antes de criar uma nova; abaixo de um limiar de similaridade, associar evidencia ao registro existente em vez de criar outro — **DECIDIDO em 23/06/2026** (`docs/decisoes_pendentes.md`, secao 5); falta calibrar o limiar com exemplos reais antes de implementar, nao so escolher um numero no escuro | Startups V4 (Auditoria e confianca) | Medio — nova checagem em `CreateStartup`, sem mudar o schema |
| `founders`/`customers`/`funding_*` nao tem origem nem confianca por campo | nenhuma lib nova: e' modelagem de dados (coluna `field_provenance`/`field_confidence` JSONB, populada quando `ExtractionTrigger` grava) | Startups V4 (Auditoria e confianca) | Medio — migration + ajuste no `Startup.update()` |

Nao adotar uma ferramenta de entity resolution pesada (ex: Dedupe.io,
Splink): o volume hoje (startups criadas via URL unica) nao justifica
infraestrutura de match probabilistico em lote — `rapidfuzz` resolve o caso
real (comparar 1 startup nova contra a base existente) com biblioteca leve.

Relacionado (campo vazio, nao duplicidade): quando `founders`/
`funding_stage`/`customers` ficam vazios porque a evidencia raspada nunca
mencionou isso, a tecnologia candidata e' uma chain de busca automatica por
mais URLs — desenhada em `docs/orchestration/roadmap_orchestration.md`
("Chain de enriquecimento por busca") e `docs/agents/roadmap_agentes.md`
(Search Planner Agent), nao neste documento.
