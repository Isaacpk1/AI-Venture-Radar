# Dividas Tecnicas

Criado em 28/06/2026. Inventario consolidado de dividas tecnicas reais
confirmadas lendo o codigo — nao especulativas. Cada item tem um arquivo
e linha de origem, um esforco estimado e um status claro.

Este documento nao e um backlog de features novas. Feature nova tem versao
propria no roadmap do modulo. Divida tecnica e o que o codigo ja deveria
fazer melhor, mas nao faz.

---

## Como ler este documento

```txt
Status  | Significado
--------|--------------------------------------------------------------
ABERTO  | confirmado no codigo, nao implementado
FECHADO | implementado (mantido aqui como registro historico)
```

Colunas da tabela:

```txt
ID      | identificador unico para referenciar em PRs/commits
Modulo  | onde o problema esta
Impacto | Alto / Medio / Baixo — efeito observavel no produto
Esforco | Alto / Medio / Baixo — custo de implementacao
Status  | ABERTO / FECHADO (data)
```

---

## Itens abertos

| ID | Modulo | Fraqueza | Abordagem | Impacto | Esforco | Status |
|---|---|---|---|---|---|---|
| DT-01 | scraping | Firecrawl citado em 4 arquivos como fallback mas nunca implementado (`strategy_selector.py`, `scraping_limits.py`, `dto.py`, `settings.py`) | Criar `FirecrawlScraper` em `infrastructure/scrapers/`, mesmo contrato de `BaseScraper`; `FIRECRAWL_API_KEY` ja existe em `Settings` | Alto — unica estrategia que cobre dominios que esgotam BS4/Playwright/Trafilatura (ex: `rapids-docs`) | Medio | FECHADO (28/06/2026) |
| DT-02 | scraping | `strategy_selector.py` tenta BS4 -> Playwright -> Trafilatura em sequencia mesmo quando o dominio sempre falha nas mesmas estrategias — custo duplicado | Circuit breaker por dominio: ler `scraping_attempts` (ja existe no banco) para pular estrategias que falharam N vezes seguidas no mesmo host | Medio — tempo e custo de rede desperdicado em re-scrapes | Medio | FECHADO (28/06/2026) |
| DT-03 | scraping | `quality_score` calculado por tentativa mas nunca logado — sem visao de distribuicao historica ou alertas de degradacao | Adicionar `log_job()` com `quality_score` e `decision` (`ACCEPT`/`LLM_REVIEW`/etc.) em `QualityScoringService`; `shared/logging` ja existe | Medio — observabilidade | Baixo | FECHADO (28/06/2026) |
| DT-04 | scraping | `ScrapingLimits.total_timeout_seconds = 90` fixo para qualquer URL — paginas de documentacao tecnica precisam de mais tempo, paginas de marketing de menos | Tornar timeout configuravel por `source_type` via `Settings`; `ScrapingJob.source_type` ja existe | Baixo-Medio | Baixo | FECHADO (28/06/2026) |
| DT-05 | scraping | `_has_captcha_challenge()` usa so heuristica de tamanho (`< 500 chars`) — falso positivo em paginas legitimas com pouco texto extraido | Adicionar segundo sinal: presenca de `<form>` com campo `g-recaptcha-response` ou `h-captcha-response` no DOM parseado; BS4 ja esta no escopo | Medio — falsos positivos rejeitam paginas validas | Baixo | FECHADO (28/06/2026) |
| DT-06 | ingestion | `TextChunker` divide por contagem de caracteres sem respeitar estrutura (titulos, listas, paragrafo semantico) — chunks cortam no meio de conceitos | Trocar por `RecursiveCharacterTextSplitter` ou `MarkdownHeaderTextSplitter` do `langchain_text_splitters` — LangChain ja e dependencia direta, zero lib nova | Alto — qualidade de retrieval RAG depende de chunks semanticamente coerentes | Baixo | FECHADO (28/06/2026) |
| DT-07 | ingestion | Mesma URL re-raspada (apos TTL de 3 dias) cria novo `Document` + novos `Chunk`s sem checar se o conteudo mudou — embeddings novos redundantes | Calcular `content_hash` do `clean_text` antes de criar `Document`; se hash igual ao ultimo `Document` da mesma URL, reaproveitar (sem criar/re-embeddear) | Medio — custo de embedding desnecessario, Qdrant cresce com duplicatas | Medio | FECHADO (28/06/2026) |
| DT-08 | rag | Filtro de busca so por `source_type` — sem filtrar por startup, data ou categoria | Estender `LexicalSearchRepository` e `VectorRepository` com filtros adicionais opcionais; sem lib nova, so mais parametros SQL/payload Qdrant | Medio — busca traz evidencias de startups nao relacionadas | Medio | FECHADO (28/06/2026) |
| DT-09 | orchestration | Etapa `ANALYZING` vai inteira para `failed` se qualquer sub-passo falhar — mesmo que `startup_id` e `evidence_attached` ja tenham sido persistidos | Registrar sub-passo que falhou em `url_ingestion_jobs` e, no retry, pular os ja concluidos (guardas de idempotencia ja existem para os 2 primeiros sub-passos) | Medio — jobs ficam em `failed` quando so o ultimo passo (briefing) falhou | Medio | FECHADO (28/06/2026) |
| DT-10 | orchestration | `TavilySearchExecutor` implementado e integrado mas nunca validado com chave real — allowlist de dominios (`BLOCKED_ENRICHMENT_HOSTS`) e ranking de candidatos calibrados so com dados sinteticos | Rodar com `TAVILY_API_KEY` real, observar URLs retornadas, ajustar allowlist e funcao `_score_enrichment_candidate()` | Medio — enriquecimento pode trazer URLs de baixa qualidade | Baixo | FECHADO (28/06/2026) |

---

## Itens fechados (historico)

| ID | Modulo | Fraqueza original | Data | Como foi resolvido |
|---|---|---|---|---|
| DT-F01 | scraping | Mesma URL sempre re-raspava completo sem cache | 23/06/2026 | `ScrapingResultRepository.get_recent_by_url()` + `SCRAPING_RESULT_CACHE_TTL = 3 dias` em `domain/policies.py` |
| DT-F02 | rag | `context_recall` 0.67 com full-text search simples (sem stemming) | 23/06/2026 | BM25 nativo via `pg_search` (ParadeDB), migration `b3f6e91c7d45`; complemento curado do catalogo NVIDIA elevou `context_recall` para `1.000000` |
| DT-F03 | rag | Modelo Cohere Rerank fixo em codigo (`rerank-v3.5`) | 23/06/2026 | `COHERE_RERANK_MODEL` em `Settings` com default `rerank-v3.5` |
| DT-F04 | orchestration | `try_extract` rodava uma vez; campo vazio ficava vazio para sempre | 26/06/2026 | `AdvanceUrlIngestionJob._schedule_enrichment_if_needed()` cria jobs filhos quando `founders`/`funding_stage`/`customers` vazios |
| DT-F05 | orchestration | Risco de loop infinito no enriquecimento | 26/06/2026 | `parent_job_id` + `enrichment_round` com `MAX_ENRICHMENT_ROUNDS = 1` |
| DT-F06 | orchestration | URL inicial fraca sem fallback de enriquecimento | 26/06/2026 | `_try_schedule_enrichment_after_scraping_failure()` cria startup minima e agenda enriquecimento mesmo quando o scraping falha |
| DT-F07 | recommendations | Match de keyword usava substring puro — `"agent"` batia dentro de `"agentes"` | 23/06/2026 | `_contains_term()` com regex `\b...\b` (word boundary) |
| DT-F08 | embeddings | Mesmo chunk re-embeddado em documentos diferentes gastava chamada extra ao provider | 23/06/2026 | Cache por `content_hash` + `model_name` via `EmbeddingJobChunkRepository.find_completed_by_content_hash()` |
| DT-F09 | embeddings | Troca de modelo de embedding podia corromper colecao Qdrant silenciosamente | 24/06/2026 | Schema guard em `_ensure_collection()`: recusa upsert se `embedding_dimension` ou `model_name` nao bater |
| DT-F10 | ingestion | `TextChunker` implementacao manual (paragrafo > sentenca > palavra) ignorava estrutura semantica; chunks podiam cortar conceitos | 28/06/2026 | `RecursiveCharacterTextSplitter` do `langchain_text_splitters` (separators `["\n\n", "\n", ". ", " ", ""]`); interface publica (`chunk_size`, `chunk_overlap`, `chunk()`) inalterada; 6/6 testes passando |
| DT-F11 | scraping | `quality_score` e `decision` calculados por tentativa mas nunca logados | 28/06/2026 | `_logger.info("scraping_attempt_scored", extra={...})` em `scraping_pipeline.py` logo antes de `attempt.finish_validation()` (e no caminho `needs_more_sources`); campos: `url`, `method`, `quality_score`, `technical_score`, `text_score`, `evidence_score`, `decision`, `source_type` |
| DT-F12 | scraping | `total_timeout_seconds = 90` fixo para qualquer URL — docs tecnicas precisam de mais tempo | 28/06/2026 | `PipelineLimits.timeout_for(source_type)` — `startup_evidence` usa `SCRAPING_STARTUP_TIMEOUT_SECONDS` (default 90s), outros usam `SCRAPING_REFERENCE_TIMEOUT_SECONDS` (default 120s); ambos em `Settings` e `.env.example` |
| DT-F13 | scraping | `_has_captcha_challenge()` nao detectava desafio em paginas longas com campo `g-recaptcha-response`/`h-captcha-response` | 28/06/2026 | `captcha_form_field_patterns` (2 regex) como sinal independente: se o campo DOM estiver presente, captcha confirmado independente do tamanho do texto; heuristica de tamanho mantida como segundo caminho; +2 testes (134 passed) |
| DT-F14 | orchestration | Allowlist de enriquecimento calibrada so com dados sinteticos; subdominio regional do LinkedIn nao era confiavel; Reddit/Medium/Quora/Glassdoor/Indeed nao bloqueados | 28/06/2026 | `BLOCKED_ENRICHMENT_HOSTS` +10 hosts (Reddit, Quora, Medium, Substack, Glassdoor, Indeed, Vagas, Catho, Yelp, Vimeo); `TRUSTED_ENRICHMENT_HOSTS` +4 (angel.co, pitchbook.com, tracxn.com, f6s.com); LinkedIn regionalizado via `host.endswith(".linkedin.com")`; `test_enrichment_scoring.py` com 26 casos de calibracao |
| DT-F15 | scraping | `FirecrawlScraper` mencionado em 4 arquivos como "futuro" mas nunca implementado — dominios que esgotam BS4/Trafilatura/Playwright nao tinham 4o fallback | 28/06/2026 | `FirecrawlScraper` (`infrastructure/scrapers/firecrawl_scraper.py`): POST `/v1/scrape` com `formats: [markdown, html]`, `onlyMainContent: true`; retorna Markdown como `raw_text`; sem `FIRECRAWL_API_KEY` a factory omite o scraper sem erro; `ScrapingMethod.FIRECRAWL` adicionado ao enum; 6 testes unitarios com `MockTransport` |
| DT-F16 | ingestion | Re-scrape pos-TTL criava `Document` + `Chunk`s novos mesmo com conteudo identico — custo de embedding redundante, Qdrant crescia com duplicatas | 28/06/2026 | `document_content_hash(clean_text)` (SHA-256 hex, `domain/entities.py`); `DocumentRepository.find_by_content_hash()` (abstrato + Postgres); `ExecuteIngestionJob` calcula hash antes de criar `Document` — se hash ja existir, chama `job.complete(existing_doc.id)` sem criar nada; migration `e3f7b2a1c9d8` (coluna `content_hash VARCHAR(64) UNIQUE NULL` em `documents`); +2 testes (dedup e presenca de hash) |
| DT-F17 | scraping | BS4 -> Playwright -> Trafilatura tentados em sequencia mesmo quando o dominio sempre falha nas mesmas estrategias — custo duplicado | 28/06/2026 | `is_circuit_open(failure_count)` em `domain/policies.py` (`CIRCUIT_BREAKER_FAILURE_THRESHOLD=3`, `CIRCUIT_BREAKER_WINDOW_HOURS=24`); `ScrapingAttemptRepository.count_recent_failures_by_host_and_method()` (abstrato + Postgres com JOIN em `scraping_jobs`); `InMemoryScrapingAttemptRepository` retorna 0 (conservador); `ScrapingPipeline._apply_circuit_breaker()` filtra estrategias tripped antes do loop principal — se TODAS tripped, usa lista completa (fallback); 9 testes unitarios em `test_circuit_breaker.py` (149 passed) |
| DT-F18 | orchestration | Etapa `ANALYZING` ia inteira para `failed` se briefing falhasse — mesmo que recommendations (cara: RAG + LLM) ja tivesse concluido, era re-executado no retry | 28/06/2026 | `recommendations_done: bool = False` em `UrlIngestionJob` (entidade + modelo + mapper); `record_recommendations(count)` persiste `recommendation_count` + `recommendations_done=True` logo apos `generate()` — antes de chamar briefing; `_run_analysis()` verifica a guarda no retry e pula recommendations; migration `f1a2b3c4d5e6` (coluna `recommendations_done BOOLEAN NOT NULL DEFAULT FALSE`); 4 testes em `test_url_ingestion_job.py` (67 passed) |
| DT-F19 | rag | Filtro de busca so por `source_type` — sem filtrar por `document_ids`, misturava evidencias de startups nao relacionadas | 28/06/2026 | `document_ids: list[UUID] \| None` adicionado a `SearchEvidenceInput`, `AnswerQuestionInput`, `LexicalSearchRepository.search()`, `VectorRepository.search()`; `QdrantVectorRepository._build_filter()` recebe ambos os params e usa `MatchAny` do SDK; `PostgresLexicalSearchRepository` reformulado pra SQL dinamico (placeholders indexados, sem f-string insegura — valores UUIDs nunca chegam como string de usuario, binds normais); lista vazia retorna `[]` sem chamar infra; `SearchEvidenceRequest`/`AnswerQuestionRequest` expostos nas rotas REST; `answer_question.py` propaga o campo; 2 testes novos (28 passed) |

---

## Ordem de implementacao recomendada

Prioridade descida pelo impacto x esforco. Itens de mesmo esforco ordenados por impacto.

```txt
1. DT-06  ingestion  TextChunker -> LangChain splitters       Baixo esforco / Alto impacto
2. DT-03  scraping   logar quality_score via shared/logging   Baixo esforco / Medio impacto
3. DT-04  scraping   timeout configuravel por source_type     Baixo esforco / Medio impacto
4. DT-05  scraping   heuristica captcha com sinal de DOM      Baixo esforco / Medio impacto
5. DT-10  orchestr.  validar Tavily real + calibrar allowlist Baixo esforco / Medio impacto
6. DT-01  scraping   Firecrawl client real                    Medio esforco / Alto impacto
7. DT-07  ingestion  dedup de Document por content_hash       Medio esforco / Medio impacto
8. DT-02  scraping   circuit breaker por dominio              Medio esforco / Medio impacto
9. DT-09  orchestr.  retry granular por sub-passo ANALYZING   Medio esforco / Medio impacto
10. DT-08 rag        filtros estruturados adicionais          Medio esforco / Medio impacto
```

---

## Criterio de entrada (o que qualifica como divida tecnica aqui)

Um item entra neste documento quando:

- foi confirmado lendo o codigo (nao e suposicao);
- o codigo ja deveria fazer diferente segundo as regras do `CLAUDE.md`;
- tem um caminho de correcao concreto sem precisar de nova feature;
- nao e apenas uma feature planejada para uma versao futura do modulo.

Features futuras ficam nos roadmaps de cada modulo.
