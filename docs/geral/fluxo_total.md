# Fluxo Total do Produto

Este documento mostra a jornada completa do NVIDIA Startup AI Radar, de uma URL
pública (ou de uma descoberta automática) até um briefing executivo apresentado
no frontend.

---

## 1. O que o produto responde

Dada uma startup pública, o sistema tenta responder, com rastreabilidade:

```txt
1. O que essa startup faz?
2. Ela tem sinais reais de IA?
3. Qual é a maturidade de IA dela (AI-native / AI-enabled / Non-AI)?
4. Quais tecnologias NVIDIA fazem sentido?
5. O encaixe é forte, moderado ou exploratório?
6. Que evidências sustentam a recomendação?
7. O que falta perguntar para qualificar melhor?
8. Como apresentar isso em um briefing executivo?
```

---

## 2. Pipeline ponta a ponta

```txt
URL pública (ou descoberta em hub)
  -> scraping            coleta + valida + persiste conteúdo aprovado
  -> ingestion           limpa texto -> Document -> Chunks
  -> embeddings          gera vetores -> Qdrant
  -> startup/evidência   cria/reusa Startup, anexa evidência aprovada
  -> extraction          extrai perfil estruturado (best-effort, LLM)
  -> classification      classifica maturidade de IA (best-effort, LLM)
  -> recommendations     cruza perfil x catálogo NVIDIA (score composto + RAG)
  -> briefing            monta briefing executivo em Markdown (+ contexto NVIDIA via RAG)
  -> frontend            apresenta job, perfil, evidências, recomendações e briefing
```

A coluna determinística do pipeline (scraping → ingestion → embeddings →
recommendations → briefing) sempre roda. As etapas de IA (validação semântica,
extraction, classification, grounding RAG, reescrita por agente) são best-effort:
sem `GEMINI_API_KEY`, o pipeline ainda entrega um resultado, só mais pobre.

---

## 3. Orquestração operacional (url_ingestion_jobs)

A jornada é coordenada pelo módulo `orchestration` através de um
`UrlIngestionJob`, cujo ciclo de vida é:

```txt
PENDING
  -> SCRAPING
  -> INGESTING
  -> EMBEDDING
  -> ANALYZING
  -> COMPLETED | FAILED
```

Cada transição assíncrona (SCRAPING/INGESTING/EMBEDDING) dispara o módulo
correspondente pela fila e faz polling via reentrega do Dramatiq. A etapa
`ANALYZING` roda numa única passagem síncrona:

```txt
cria ou reaproveita startup (dedup por nome/domínio)
anexa evidência aprovada
extrai perfil estruturado (try_extract, best-effort)
classifica maturidade de IA (try_classify, best-effort)
agenda enriquecimento se faltam sinais (founders/funding/customers)
gera recomendações NVIDIA
gera briefing executivo
salva startup_id, recommendation_count e briefing_id no job
```

Um gate por `source_type` controla quem entra em `ANALYZING`: só
`startup_evidence`. Fontes curadas (`nvidia_knowledge`) completam logo após o
embedding — elas alimentam o RAG, não viram startup.

---

## 4. Enriquecimento automático

Quando o scraping falha ou produz fonte fraca, ou quando o perfil extraído ainda
tem `missing_signals`, a orquestração agenda jobs de enriquecimento:

```txt
gera queries (Search Planner Agent ou heurística determinística)
busca URLs externas (Tavily, opcional) + URLs do mesmo domínio
filtra/pontua candidatos (descarta redes sociais/wikipedia; prioriza Crunchbase/LinkedIn)
cria UrlIngestionJobs filhos (parent_job_id + enrichment_round, máximo 1 round)
```

---

## 5. Caminho da descoberta automática

Em vez de uma URL avulsa, o sistema pode descobrir startups sozinho:

```txt
POST /startup-discovery/runs
  -> extratores de hubs públicos (InovAtiva Brasil, Abstartups, 100 Open Startups)
  -> URLs descobertas (limitadas por STARTUP_DISCOVERY_MAX_PER_RUN)
  -> cria url_ingestion_jobs (source_type=startup_evidence)
  -> o pipeline da seção 2/3 cuida do resto
GET /startup-discovery/runs/{id}   acompanha urls_found / jobs_submitted / status
```

---

## 6. Caminho do conhecimento NVIDIA (alimenta o RAG)

```txt
catálogo estático de tecnologias NVIDIA (18 itens, em código)
registry de fontes oficiais (20 fontes: docs NIM, Triton, NeMo, RAPIDS, etc.)
POST /nvidia-knowledge/ingestion/jobs
  -> url_ingestion_jobs com source_type=nvidia_knowledge
  -> scraping -> ingestion -> embeddings (NÃO entra em ANALYZING)
  -> conteúdo recuperável via /rag/search?source_type=nvidia_knowledge
```

Esse conteúdo é o que `recommendations` e `briefing` consultam por RAG para
fundamentar justificativas com citações reais.

---

## 7. Subfluxo de busca e resposta (RAG)

```txt
query
  -> embedding da query (Gemini)
  -> busca vetorial no Qdrant
  -> busca lexical no PostgreSQL via pg_search (BM25 nativo)
  -> fusão RRF (Reciprocal Rank Fusion)
  -> reranking Cohere (opcional)
  -> evidências ordenadas

pergunta
  -> search_evidence (acima)
  -> answer generator Gemini
  -> resposta com citações
```

---

## 8. Onde cada módulo entra no fluxo

```txt
scraping          passo 1 (coleta)
ingestion         passo 2 (documents/chunks)
embeddings        passo 3 (vetores/Qdrant)
startups          passo 4-6 (startup, evidência, extract, classify)
nvidia_knowledge  catálogo + fontes que alimentam o RAG
rag               busca/resposta consultada por recommendations e briefing
recommendations   passo 7 (recomendações NVIDIA)
briefing          passo 8 (briefing executivo + PDF)
orchestration     coordena todos os passos (url_ingestion_jobs / analysis_jobs)
startup_discovery alimenta o início do pipeline em lote
agents            executa o julgamento de LLM dentro de vários passos
frontend          apresenta tudo e opera o pipeline
```

Documentos relacionados: `arquitetura_monolito_modular_workers.md`,
`comunicacao_entre_modulos.md`, `stack_e_onde_e_usado.md`.
