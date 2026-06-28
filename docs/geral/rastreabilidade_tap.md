# Rastreabilidade TAP → Implementação

Matriz que cruza, requisito por requisito, o **Termo de Abertura do Projeto**
("Projeto: NVIDIA Startup AI Radar") com o que está implementado no código.
Cada linha tem **status**, **onde foi entregue** (módulo/versão) e **evidência**
verificável (rota, arquivo, migration ou teste).

Legenda de status: ✅ Atendido · 🟡 Parcial · ⚪ Fora de escopo (decisão registrada)

Data: 2026-06-28 · Fonte do escopo: `Projeto_ NVIDIA Startup AI Radar.pdf`

---

## 1. Objetivo do projeto (TAP §2)

O TAP pede um sistema capaz de seis coisas. Todas estão cobertas pela jornada
ponta a ponta da Orchestration V2 (URL bruta → briefing, sem operação manual).

| Capacidade exigida (TAP §2) | Status | Onde | Evidência |
|---|---|---|---|
| Encontrar startups BR com sinais de uso intensivo de IA | 🟡 | Startup Discovery V1 | `POST /startup-discovery/runs`; 3 hubs (InovAtiva, Abstartups, 100 Open Startups) dos ~17 listados |
| Coletar dados públicos (empresa, produto, setor, clientes, funding, founders, tecnologias) | ✅ | Scraping V8 + Extraction Agent V8 + Startups V2/V4 | Campos `founders`/`funding_stage`/`customers`/`sector`/`description` + `field_evidence_ids` |
| Avaliar gaps na stack de IA | ✅ | Recommendations V4/V5 | `missing_signals` por recomendação + `signal_origins` |
| Consultar base de conhecimento NVIDIA | ✅ | NVIDIA Knowledge V2 + RAG V4 | `/rag/answer?source_type=nvidia_knowledge` |
| Recomendar tecnologias NVIDIA adequadas ao perfil | ✅ | Recommendations V1–V5 | `POST /recommendations`; score composto 5 dimensões |
| Gerar briefing executivo | ✅ | Briefing V4 | `POST /briefings`; briefing analítico em 12 seções |

---

## 2. Escopo da solução (TAP §4)

> "Pipeline multi-agente: buscar empresas → coletar → estruturar → classificar
> maturidade AI-native → consultar RAG NVIDIA → gerar recomendações."

✅ **Atendido.** O fluxo do TAP é o pipeline real da Orchestration V2:
`scraping → ingestion → embeddings → startup → evidência → extract → classify →
recommendations → briefing`. O TAP libera o frontend; o projeto entregou um
frontend completo (V5) mesmo assim.

---

## 3. Agentes LangGraph (TAP §5.1) — os 8 sugeridos

| Agente sugerido (TAP) | Status | Versão | Evidência |
|---|---|---|---|
| Search Planner Agent | ✅ | Agents V3 | `SearchPlanningGraph` (`graphs/search_planning/`) |
| Scraper Agent | ✅ | Scraping V8 | Módulo `scraping` determinístico + `SemanticInvestigator` (AGENT_REVIEW) |
| Extractor Agent | ✅ | Agents V8 | `ExtractionGraph`; contrato `ExtractionService` |
| Startup Classifier Agent | ✅ | Agents V9 | `StartupClassificationGraph`; AI-native/AI-enabled/Non-AI |
| Evidence Validator Agent | ✅ | Agents V2 | `EvidenceValidationGraph` |
| NVIDIA RAG Agent | ✅ | Agents V10 | `NvidiaRagGraph`; usa `rag` como tool |
| Recommendation Agent | ✅ | Agents V11 | `RecommendationAgentGraph`; consumidor síncrono em orchestration |
| Briefing Agent | ✅ | Agents V12 | `BriefingAgentGraph`; persiste prosa reescrita no banco |

**Recursos LangGraph pedidos (estado, nós, transições condicionais, checkpoints,
retry, intervenção humana):** ✅ todos presentes — checkpoint PostgreSQL
(`AsyncPostgresSaver`, migration `9e1f3b5c8a2d`), `waiting_human_review` +
`interrupt()` real (Agents V6/V7), limites obrigatórios por grafo
(`max_iterations`, `max_tool_calls`, `timeout_total`).

---

## 4. Scraping e coleta (TAP §5.2)

| Tecnologia recomendada (TAP) | Status | Evidência |
|---|---|---|
| Playwright (sites dinâmicos) | ✅ | Scraping V4; `PlaywrightScraper` |
| BeautifulSoup (HTML simples) | ✅ | Scraping V1 |
| trafilatura (texto principal) | ✅ | Scraping V6 |
| Firecrawl (extração limpa p/ RAG) | 🟡 | `FIRECRAWL_API_KEY` previsto; não plugado (gap conhecido em `rapids-docs`) |
| Scrapy (crawling em escala) | ⚪ | Não usado — volume de case/demo não justifica |

Rastreabilidade de fontes (exigida pelo TAP): ✅ cada `ScrapingResult` mantém a
URL de origem; evidências carregam `source_url` até a UI.

---

## 5. RAG com reranking (TAP §5.3) — pipeline de 9 passos

| Passo (TAP) | Status | Evidência |
|---|---|---|
| 1. Ingestão de documentos | ✅ | Ingestion V1 (`documents`, `chunks`) |
| 2. Limpeza/normalização | ✅ | `TextCleaner` |
| 3. Chunking semântico | ✅ | `TextChunker` (2000 chars, overlap 200, respeita parágrafos) |
| 4. Geração de embeddings | ✅ | Embeddings V2 (Gemini `gemini-embedding-001`) |
| 5. Vector database | ✅ | Qdrant (Embeddings V3) |
| 6. Busca híbrida (vetorial + lexical) | ✅ | RAG V3 — Qdrant + BM25 nativo (`pg_search`/ParadeDB), fusão RRF |
| 7. Reranking | ✅ | RAG V4 — Cohere Rerank (`rerank-v3.5`) |
| 8. Resposta com citações | ✅ | RAG V2 — `/rag/answer` com citações |
| 9. Avaliação de qualidade | ✅ | Ragas baseline (faithfulness 0.92, context_precision 0.90, context_recall 0.67) |

| Banco/lib recomendado (TAP) | Status | Evidência |
|---|---|---|
| Qdrant (ou alternativa) | ✅ | Qdrant |
| PostgreSQL (dados estruturados) | ✅ | PostgreSQL (source of truth) |
| BM25 (busca lexical) | ✅ | BM25 via `pg_search` (operador `@@@` + `paradedb.score()`) |
| Cohere Rerank | ✅ | `CohereReranker` |

---

## 6. Base de conhecimento NVIDIA (TAP §5.4) — 16 tecnologias

✅ As 16 entradas do TAP estão no catálogo (`nvidia_knowledge/catalog_data.py`):
Inception, NIM, NeMo, NeMo Guardrails, Triton, TensorRT-LLM, RAPIDS, cuDF, cuML,
CUDA, Riva, Omniverse, Isaac, Clara, Morpheus, AI Enterprise.

Além do catálogo estático, o NVIDIA Knowledge V2 ingere **fontes oficiais reais**
no RAG: 20 fontes processadas, **17 com conteúdo recuperável**. 🟡 3 gaps por
rede/DNS do ambiente (`nvidia-nim-docs`, `monai-docs`, `rapids-docs`) — limitação
de ambiente, não de código.

---

## 7. Motor de recomendação (TAP §5.5) — output exigido

O TAP exige 7 campos no output da recomendação:

| Campo exigido (TAP) | Status | Onde |
|---|---|---|
| Tecnologias NVIDIA recomendadas | ✅ | `Recommendation.technology_slug` |
| Justificativa técnica | ✅ | `justification` fundamentada via RAG (Recommendations V2) |
| Justificativa de negócio | ✅ | Reescrita pelo Recommendation Agent (V11) em linguagem de negócio |
| Nível de prioridade | ✅ | `priority` ordinal (Recommendations V3) |
| Complexidade de implementação | ✅ | `complexity` low/medium/high (Recommendations V3) |
| Próxima ação sugerida | ✅ | `suggest_next_actions()` no briefing (Briefing V1/V4) |
| Evidências usadas | ✅ | `evidence_ids` + `signal_origins` (rastreável até a fonte) |

Os exemplos de mapeamento do TAP §5.5 (LLM em atendimento → NIM/Guardrails/Triton;
tabular → RAPIDS/cuDF/cuML; voz → Riva; saúde → Clara/MONAI; etc.) estão
codificados e validados pelo **golden set** (Briefing V5): 6 arquétipos,
média p@3 = 0.78.

---

## 8. Arquitetura proposta (TAP §6)

✅ O fluxo de alto nível do TAP (Consulta → Search Planner → Scraper → Extractor →
Banco estruturado → Classifier → Evidence Validator → Diagnóstico → NVIDIA RAG →
Reranker → Recommendation → Briefing → Interface web) corresponde 1:1 à jornada
da Orchestration V2 + Frontend. Ver `docs/geral/fluxo_total.md`.

---

## 9. Fontes de scraping de empresas (TAP §7)

🟡 **Parcial por decisão.** Dos hubs listados, o Startup Discovery V1 implementa
**InovAtiva Brasil, Abstartups e 100 Open Startups**. Os demais (StartSe, Distrito,
Latitud, Cubo, ACE, Endeavor, Bossa, Anjos do Brasil, Darwin, Liga, WOW) e as
fontes de notícias (§7.2) não foram implementados — a arquitetura de extractor por
hub (`HubLinkExtractor` + seletores) permite adicioná-los sem mudar a lógica.

---

## 10. Fontes da base NVIDIA (TAP §8)

🟡 As documentações oficiais NVIDIA (§8.2) entraram no `NvidiaKnowledgeSourceRegistry`
(20 fontes, 17 recuperáveis). Os materiais de apoio em vídeo/artigo (§8.1 — Sequoia,
Emergence, 5-layer cake, playlists do YouTube) não foram transcritos/ingeridos.

---

## 11. Entregáveis esperados (TAP §9)

| Entregável (TAP) | Status | Evidência |
|---|---|---|
| **E1** — Pipeline de scraping | ✅ | Scraping V8 (138 testes); `POST /url-ingestion/jobs` |
| **E2** — Multiagente LangGraph | ✅ | Agents V12, 8 agentes; checkpoint + human-in-the-loop |
| **E3** — RAG NVIDIA com reranking + citações | ✅ | RAG V4 (híbrido + Cohere + citações + Ragas) |
| **E4** — Motor de recomendação | ✅ | Recommendations V5 (score composto 5 dimensões) |
| **E5** — Interface web | ✅ | Frontend V5 (portfólio, jobs, dashboard, chatbot, export PDF, revisão humana) |
| **E6** — Diferencial do projeto | ✅ | Rastreabilidade ponta a ponta + orquestração automática + revisão humana + dashboard de BI + observabilidade Langfuse |

---

## 12. Diferenciais entregues além do TAP

Itens que o TAP não exige (ou só sugere) e que o projeto entregou:

- **Avaliação de qualidade do RAG** com Ragas (o TAP cita "avaliação" como passo 9, sem ferramenta) e **golden set** de recomendações com p@3.
- **Observabilidade**: logs com correlação por job + tracing de LLM via Langfuse self-hosted.
- **Orquestração automática** (URL bruta → briefing sem operação manual) + **enriquecimento automático** quando o scraping falha.
- **Revisão humana** de recomendações e briefings (pending/approved/rejected).
- **Dedup de startups** por nome/domínio (rapidfuzz, limiar calibrado com 17 pares reais).
- **Export de briefing em PDF** preservando citações.
- **Dashboard de BI**: distribuição de maturidade + top tecnologias + comparação + fila em lote.

---

## 13. Conformidade resumida

| Bloco do TAP | Conformidade |
|---|---|
| Objetivo (§2) | ✅ 6/6 capacidades (descoberta parcial nos hubs) |
| Escopo / pipeline (§4, §6) | ✅ completo |
| Agentes LangGraph (§5.1) | ✅ 8/8 |
| Scraping (§5.2) | ✅ núcleo (Firecrawl/Scrapy fora) |
| RAG com reranking (§5.3) | ✅ 9/9 passos |
| Base NVIDIA (§5.4) | ✅ 16/16 techs; 17/20 fontes recuperáveis |
| Recomendação (§5.5) | ✅ 7/7 campos de output |
| Fontes BR (§7) | 🟡 3 hubs implementados |
| Fontes NVIDIA (§8) | 🟡 docs oficiais sim; vídeos não |
| Entregáveis (§9) | ✅ 6/6 |

**Fora de escopo (decisão registrada em `docs/geral/dividas_tecnicas.md`):** auth,
CI/CD, deploy de produção — o projeto é case/demo, não alvo de produção.
