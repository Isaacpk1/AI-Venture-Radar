# Módulo Orchestration — Visão Geral

## 1. Importância

O `orchestration` coordena a jornada inteira do produto, principalmente a partir
de uma URL bruta. É ele que transforma "uma URL" em "um briefing", encadeando
scraping → ingestion → embeddings → startup → recomendações → briefing sem
operação manual entre etapas. Também cuida do enriquecimento automático quando os
sinais são fracos e da limpeza de vetores órfãos.

## 2. Fluxo (url_ingestion_jobs)

```txt
PENDING -> SCRAPING -> INGESTING -> EMBEDDING -> ANALYZING -> COMPLETED | FAILED
```

Na etapa `ANALYZING` (uma passagem síncrona):

```txt
cria/reusa startup -> anexa evidência -> try_extract + try_classify
-> agenda enriquecimento se faltam sinais -> recommendations.generate()
-> briefing.generate() -> salva startup_id/recommendation_count/briefing_id
```

Gate por `source_type`: só `startup_evidence` entra em ANALYZING; fontes curadas
(`nvidia_knowledge`) completam após o embedding. A fila `url_ingestion` é o
próprio loop de polling (reentrega Dramatiq até estado terminal).

## 3. Estrutura de pastas

```txt
orchestration/
  presentation/     POST/GET analysis/jobs, url-ingestion/jobs, /advance
  application/      use_cases (AdvanceUrlIngestionJob), ports
  domain/           AnalysisJob, UrlIngestionJob (status + parent_job_id/enrichment_round), exceções
  infrastructure/   startups_adapters/, agents_adapters/ (enriquecimento), queue/
  factories/        importa Recommendations/Briefing/Startups/Embeddings/AgentsFactory
  tests/
```

## 4. Stack

```txt
Dramatiq + Redis    fila url_ingestion como loop de polling
Tavily (reuso)      busca externa para enriquecimento (opcional)
```

## 5. Histórico de versões

| Versão | Status | Entrega |
|---|---|---|
| V1 | Entregue | analysis_jobs a partir de startup_id (recommendations -> briefing) |
| V2 | Entregue | URL bruta ponta a ponta: scraping ... -> briefing; worker automático; jornada completa |
| V2.1 | Entregue | Enriquecimento por URLs do mesmo domínio |
| V2.2 | Entregue | Busca externa Tavily opcional + resgate de fonte fraca |

**Versão atual: V2.2.** Também: histórico global de jobs, limpeza de vetores
órfãos. Detalhes em `versoes/`; futuro (V3 retry por etapa, V4 notificações) em
`roadmap.md`.
