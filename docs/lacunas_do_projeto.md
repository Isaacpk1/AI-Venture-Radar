# Lacunas do Projeto

Criado em 23/06/2026, a partir de leitura direta do codigo (nao so dos
roadmaps por modulo — varios itens abaixo ja estavam espalhados em 11
documentos diferentes; este arquivo junta tudo num lugar so). Cada item
tem status real, verificado agora, nao copiado de uma entrega antiga:

```txt
[ABERTO]      lacuna confirmada, sem decisao tomada ainda
[DECIDIDO]    decisao ja tomada em docs/decisoes_pendentes.md, falta implementar
[FORA-ESCOPO] decisao consciente de nao corrigir agora (projeto e' demo)
[RESOLVIDO]   ja foi corrigido nesta mesma sessao de trabalho — listado so
              pra nao reabrir por engano
```

---

## 1. Observabilidade — a lacuna mais ampla do projeto

```txt
[ABERTO]
```

Confirmado agora por grep (`bind_context`/`log_job`/`get_logger`): **so 1
use case em todo `apps/api/src/modules/` loga estruturado** —
`orchestration/application/use_cases/advance_url_ingestion_job.py`. Os 5
workers (`tasks.py`) logam no ponto de entrada. Todo o resto — `scraping`,
`ingestion`, `embeddings`, `agents`, `startups`, `rag`, `recommendations`,
`briefing`, `nvidia_knowledge` — **zero log estruturado dentro da logica de
negocio**. A infraestrutura existe (`shared/logging/`) desde a Fase 0 do
`roadmap_evolucao_tecnica_mvp.md), so nao foi instrumentada na maioria dos
lugares.

Custo/latencia/tokens de LLM: nenhum agente ou gerador registra isso hoje,
exceto a estimativa heuristica de `embeddings` (`estimate_input_tokens()`,
nao e' uso real reportado pela API).

Impacto: depurar uma falha em `recommendations`/`briefing`/`startups` hoje
exige ler codigo + consultar Postgres na mao — exatamente o problema que a
Fase 0 quis resolver, mas resolveu so na borda (workers), nao no miolo.

---

## 2. RAG e qualidade de busca

```txt
[RESOLVIDO] em 24/06/2026 (os 2 itens que estavam abertos aqui)
```

- `recommendations` e `briefing` usam adaptadores RAG
  (`RagNvidiaKnowledgeGrounder`/`RagNvidiaContextGrounder`) que consultam
  `RagQuestionAnswerer` com `source_type=nvidia_knowledge`, preservando
  fallback deterministico quando nao ha contexto recuperavel — ver
  `docs/recommendations/recommendations_v2_rag_grounding.md`.
- `context_recall` tinha sido medido em 0.67 via Ragas (o mais fraco dos 4
  indicadores), o que motivou trocar `ts_rank` por `pg_search`/ParadeDB.
  **Correcao:** esta entrada dizia "confirmado que nada disso existe em
  codigo ainda" — isso estava errado mesmo na data em que foi escrito; o
  BM25 nativo (migration `b3f6e91c7d45`,
  `PostgresLexicalSearchRepository` reescrito pro operador `@@@`) ja
  tinha sido implementado em 23/06/2026, ver
  `docs/rag/roadmap_rag.md`. Pendente real: medir o `context_recall` pos-
  troca via Ragas (`RUN_RAGAS_EVAL=1`, custo de API) contra o baseline
  0.67 — ainda nao foi rodado.
- Sem filtro por `startup_id` no RAG — nao e' lacuna pro que foi decidido
  (RAG vai fundamentar contexto NVIDIA, filtrado por `source_type`, nao
  por startup), mas continua sendo lacuna real se um chat por startup
  especifica avancar no frontend depois.

---

## 3. Risco de dados (Postgres / Qdrant)

```txt
[RESOLVIDO] em 25/06/2026 (os 2 itens que estavam parcialmente abertos aqui)
```

- `model_name` fica salvo no payload do Qdrant (confirmado,
  `qdrant_vector_repository.py:49,100`) mas **nunca e usado como filtro ou
  guarda** — se o modelo de embedding trocar de novo com dados existentes,
  nada impede um upsert de dimensao incompativel quebrar a colecao.
  Protecao entregue em 23/06/2026: a colecao registra modelo e dimensao como
  metadata e recusa escritas incompativeis ou colecoes legadas sem schema.
- Payload do Qdrant duplica `source_url`/`source_type` do Postgres sem
  mecanismo de sincronia se a evidencia for editada depois. **Correcao em
  25/06/2026:** essa entrada presumia um fluxo de edicao que, investigado
  agora, nao existe no codigo — `Document`/`ScrapingResult` sao write-once
  (so `save()`). Em vez de construir codigo sem chamador real, implementado
  o gatilho real equivalente: `VectorRepository.delete_by_document_id()` +
  `AdvanceUrlIngestionJob._cleanup_superseded_vectors()` removem do Qdrant
  os vetores de um `Document` superado quando a mesma URL e' re-raspada
  apos o cache de 3 dias expirar (antes ficavam orfaos pra sempre). Ver
  `docs/embeddings/roadmap_embeddings.md` e
  `docs/orchestration/roadmap_orchestration.md`.

```txt
[FORA-ESCOPO]
```
- Backup/snapshot do Qdrant — decidido nao fazer agora (projeto e' demo).

---

## 4. Scraping

```txt
[ABERTO] — nenhuma decisao tomada ainda sobre estes
```

- Sem circuit breaker por dominio: `strategy_selector.py` tenta
  BS4 -> Playwright -> Trafilatura sequencialmente mesmo quando o padrao
  de falha (captcha em todas) ja indica que nenhuma vai funcionar.
- Firecrawl citado em comentario (`strategy_selector.py`,
  `scraping_limits.py`, `dto.py`) mas nunca implementado de fato — e' o
  unico fix de codigo possivel pro gap conhecido de `rapids-docs` (NVIDIA
  Knowledge V2).
- Heuristica de captcha (`_has_captcha_challenge()`) ainda baseada em
  `< 500 chars` de texto extraido, nao em sinal real de captcha.
- `quality_score` calculado mas nunca persistido como serie — sem
  dashboard de distribuicao ao longo do tempo (a infra de logging existe
  desde a Fase 0, so nao foi usada aqui).

```txt
[RESOLVIDO] — nao reabrir
```
- Cache por URL (TTL 3 dias) — implementado, testado, em produção.

---

## 5. Ingestion

```txt
[ABERTO]
```

- `TextChunker` ainda corta por contagem de caracteres, nao respeita
  estrutura (titulos, listas) — `langchain_text_splitters` mapeado como
  candidata, nao implementado.
- Sem dedup de `Document` por hash do `clean_text` — duas URLs com o mesmo
  texto (ex: mesma pagina raspada via URL levemente diferente) geram dois
  documentos e dois lotes de chunks. Precisaria de migration nova
  (`documents` nao tem coluna de hash hoje).

---

## 6. Startups

```txt
[RESOLVIDO] em 25/06/2026
```
- Dedup por nome/website com `rapidfuzz` — implementado (Startups V4,
  slice inicial). `domain/policies.py::find_duplicate_startup()` compara
  por dominio normalizado (exato, sem fuzzy) e por nome via
  `rapidfuzz.fuzz.WRatio()` com `NAME_SIMILARITY_THRESHOLD = 92.0`,
  calibrado com 17 pares reais antes de escrever qualquer logica. Ver
  `docs/startups/roadmap_startups.md` e
  `test_startup_deduplication_policy.py`. `requirements.txt` inclui
  `rapidfuzz>=3.0,<4`.

```txt
[ABERTO]
```
- Sem confianca/origem por campo extraido (`founders`/`funding`/
  `customers` nao sabem qual evidencia/fonte os preencheu) — V4 do modulo
  (resto da fatia), ainda futuro, sem decisao de prioridade.

---

## 7. Agents

```txt
[DECIDIDO] (docs/decisoes_pendentes.md, secao 6)
```
- NVIDIA RAG Agent (V10) sem consumidor real — decidido deixar como esta,
  nao redesenhar o grafo. Ja documentado como decisao fechada.
- Search Planner Agent (V3) existe e gera queries quando uma evidencia e'
  insuficiente, mas ainda nao existe executor de busca web. Estado real: a
  orquestracao ja cria ate 2 `url_ingestion_jobs` filhos no mesmo dominio
  quando `founders`/`funding_stage`/`customers` seguem vazios; o que falta e'
  transformar queries do Search Planner em URLs externas candidatas. Ver
  `docs/agents/roadmap_agentes.md` e
  `docs/orchestration/roadmap_orchestration.md` ("Chain de enriquecimento por
  busca").

```txt
[ABERTO]
```
- `asyncio.timeout` por `agent_run` — a regra ja existe no `CLAUDE.md`
  ("todo grafo deve definir timeout_total"), mas nao esta aplicada no
  codigo (`execute_agent_job.py`). Nenhum agente tem limite real de tempo
  de execucao hoje.
- Sem circuit breaker por agente — se o Gemini cair, os 7 agentes falham
  individualmente sem nenhuma protecao agregada.

---

## 8. NVIDIA Knowledge

```txt
[ABERTO]
```
- 3 fontes sem fix de codigo possivel agora: `nvidia-nim-docs` e
  `monai-docs` (DNS intermitente do lado Windows — ambiente, nao codigo),
  `rapids-docs` (esgotou as 3 estrategias de scraping — precisa de
  Firecrawl real, ver secao 4).
- Sem health-check periodico das 20 URLs do registry — nada avisa se uma
  fonte curada saiu do ar antes de alguem tentar reingerir.

---

## 9. Frontend

```txt
[RESOLVIDO] em 23/06/2026
```
- Vitest + React Testing Library foram instalados e configurados. Ha 23
  testes (reconferido 24/06/2026, +9 do fechamento do Frontend V3) para
  `UrlSubmissionForm`, `JobStatusPanel`, `StartupDetails`,
  `StartupPortfolio`, `JobHistory` e `NvidiaChat`.
- **Correcao em 23/06/2026:** este documento afirmava um "bug real
  confirmado de Rules of Hooks em `StartupDetails`" — lendo o arquivo na
  integra, isso nao se confirma (hooks chamados corretamente, antes de
  qualquer `return` condicional). Removido daqui; o gap real e' so a
  ausencia de testes.

```txt
[RESOLVIDO] em 24/06/2026 — Frontend V3 completo
```
- Listagem/cards de startups: `GET /startups` paginado com busca/filtros
  + pagina `/startups` (`features/startups/startup-portfolio.tsx`).
- Historico global de jobs: `UrlIngestionJobRepository.list_page()` novo
  + `GET /url-ingestion/jobs` paginado + pagina `/jobs`
  (`features/jobs/job-history.tsx`).
- Badge de fit consolidado + evidencia clicavel por recomendacao em
  `startup-details.tsx` (regra pura no frontend, sem chamada nova a
  API); achado real durante a implementacao — `customers` da `Startup`
  existia na API desde a V2 mas nunca era renderizado, corrigido junto.
- Chatbot sobre NVIDIA Knowledge (`features/knowledge/nvidia-chat.tsx` +
  pagina `/knowledge`) — so UI, `POST /rag/answer` ja existia.
- Export do briefing em PDF (`GET /briefings/{id}/export`) — **decisao
  tecnica registrada**: trocado `weasyprint` (planejado) por Playwright +
  Jinja2 + `markdown`, ver `docs/briefing/briefing_v3_export_pdf.md`.
- Validado end-to-end via `httpx.AsyncClient` contra a app real (PDF de
  28KB gerado, `%PDF-1.4`); `next build`/`tsc --noEmit` sem erro.
  Validacao visual em navegador ficou pendente nesta sessao — limitacao
  de ambiente (WSL nao alcanca processos Windows pela rede), nao bug.

```txt
[RESOLVIDO] em 25/06/2026 - Frontend V4 completo
```
- Dashboard `/dashboard` com graficos SVG/HTML de maturidade e top tecnologias.
- `GET /startups/stats` e `GET /recommendations/stats` entregues.
- Comparacao de ate 3 startups e fila em lote entregues.

```txt
[ABERTO/planejado]
```
- Frontend V5 (revisao humana, sem auth completa).

---

## 10. Qualidade de engenharia transversal

```txt
[FORA-ESCOPO] (projeto e' demo, ver docs/decisoes_pendentes.md secao 1)
```
- Sem CI (`.github/workflows/` nao existe), sem `mypy`/`ruff`/`pyproject.toml`
  configurado (confirmado agora, nenhum dos dois existe), sem
  Dockerfile de deploy pra API/workers, sem autenticacao.

---

## 11. Seguranca — nem tudo e' lacuna

```txt
[PONTO FORTE, confirmado agora — nao e' lacuna]
```
- `UrlGuard` (`scraping/infrastructure/security/url_guard.py`) esta bem
  implementado: valida esquema (so http/https), resolve DNS de verdade
  antes de aceitar (nao confia so no texto da URL), e usa
  `ipaddress.is_global` pra rejeitar qualquer IP privado/loopback/
  link-local (cobre `169.254.169.254`, metadados de nuvem, RFC-1918, etc.)
  — exatamente o que a regra de seguranca do `CLAUDE.md` pede.

```txt
[ABERTO]
```
- Sem rate limiting nem CORS configuravel em nenhuma rota.
- Sem validacao de redirect explicita confirmada alem da 1a resolucao de
  DNS (precisa reconfirmar se o `UrlGuard` e' rechamado a cada redirect
  HTTP seguido pelo scraper, ou so na URL original).

---

## Resumo por status

| Status | Quantidade de itens |
|---|---|
| RESOLVIDO (24-25/06/2026) | 7 (cache de scraping, fundacao de testes do frontend, RAG grounding em recommendations/briefing, Frontend V3 completo, P3 decidido+implementado, limpeza de vetores orfaos no Qdrant — redefinicao da "sincronia Qdrant<->Postgres", e dedup de startups com `rapidfuzz` — Startups V4 slice inicial) — varios outros (rag->embeddings, caches de embeddings, agent wiring, Cohere config, BM25/pg_search) ja foram resolvidos em sessoes anteriores e nem entraram aqui |
| DECIDIDO, falta implementar | 6 (rapidfuzz saiu — implementado em 25/06/2026; Frontend V3 saiu — entregue por completo) |
| ABERTO, sem decisao ainda | 11 |
| FORA-ESCOPO (demo) | 2 grupos (producao transversal, backup Qdrant) |

## Como usar este documento

Mesma regra do `decisoes_pendentes.md`: quando um item for implementado,
mover pro `CLAUDE.md`/roadmap do modulo com data, e apagar daqui. Itens
`[ABERTO]` que ganharem decisao migram pra
`docs/decisoes_pendentes.md` primeiro, nao direto pra implementacao.
