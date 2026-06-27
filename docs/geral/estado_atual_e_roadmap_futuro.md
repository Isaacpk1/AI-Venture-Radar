# Estado Atual do Projeto e Roadmap Futuro

Atualizado em 27/06/2026. Este documento descreve onde o NVIDIA Startup AI Radar
está hoje e o que ainda falta. Ponto importante: **não existe uma versão global
única do produto** — cada módulo evoluiu numa trilha própria, então o sistema tem
módulos em V12, V8, V5, V4, V2 e V1 ao mesmo tempo.

---

## 1. Versão por módulo

| Módulo | Versão atual | Status | Resumo |
|---|---:|---|---|
| API / Backend | 0.1.0 | Entregue | FastAPI modular com routers por módulo e healthcheck |
| Scraping | V8 | Entregue | Coleta com persistência, fila, validação determinística + semântica + agent review |
| Agents | V12 | Entregue | Sistema multiagente LangGraph com os 8 agentes do brief original |
| Ingestion | V1 + V4 | Entregue | V1 documents/chunks; V4 worker assíncrono |
| Embeddings | V5 | Entregue | Embeddings, Qdrant, worker em lote, métricas, cache, reembedding |
| Startups | V4.1 | Entregue | Relacional, evidências, campos estruturados, classificação, dedup, StartupAIProfile |
| RAG | V4 + V5 parcial | Entregue/parcial | V4 busca híbrida + reranking; V5 avaliação Ragas opt-in |
| NVIDIA Knowledge | V2 | Entregue | Catálogo + registry de fontes oficiais (20/20 processadas, 17/20 com conteúdo) |
| Recommendations | V4/V5 | Entregue | Score composto, confiança nova, sinais, nível, faltando, RAG grounding, stats |
| Briefing | V4 | Entregue | Briefing analítico, tese de fit, matriz, fortes vs exploratórias, perguntas, PDF |
| Orchestration | V2.2 | Entregue | URL até briefing, enriquecimento por domínio, busca Tavily opcional |
| Startup Discovery | V1 | Entregue | Descoberta em hubs públicos → url_ingestion_jobs |
| Frontend | V5 | Entregue | Jornada, portfólio, dashboard, chat, PDF, lote, review simples |
| Workers | Base completa | Entregue | Dramatiq para scraping, agents, ingestion, embeddings, orchestration |
| Observabilidade | Fundação | Parcial | Logging estruturado + Langfuse opcional; sem alertas/retenção de produção |

---

## 2. O que está pronto e funcionando

O MVP backend + frontend por URL está funcional ponta a ponta:

```txt
URL -> scraping -> ingestion -> embeddings -> startup/extract/classify
-> recommendations -> briefing -> frontend
```

Também entregues: portfólio paginado, histórico global de jobs, dashboard de
portfólio (distribuição de maturidade + top tecnologias), comparação de até 3
startups, fila de análise em lote, chatbot sobre NVIDIA Knowledge, export de
briefing em PDF, revisão humana simples (pending/approved/rejected) e Startup
Discovery V1.

### Estado dos testes

```txt
Backend:  ~617 testes coletados; com infra viva, 559 passed, 1 skipped (Ragas opt-in)
Frontend: 32 passed (Vitest)
```

Comandos:

```txt
venv/Scripts/python.exe -m pytest apps/api/src/modules/ apps/api/src/shared/ -q
npm run test -- --run   (em apps/web/)
```

---

## 3. Banco e migrations

Head atual: `b4c8e2f1a9d7` (coluna `ai_profile` JSONB em startups).

Tabelas principais:

```txt
scraping_jobs / scraping_attempts / scraping_results
agent_runs / agent_steps / checkpoints (+ blobs/writes/migrations)
ingestion_jobs / documents / chunks
embedding_jobs / embedding_job_chunks
startups / startup_evidences
recommendations / briefings / analysis_jobs
url_ingestion_jobs / startup_discovery_runs
```

---

## 4. Limites atuais (fora de escopo do case/demo)

```txt
auth real (decidido fora de escopo — projeto é demo)
CI/CD e deploy de produção
backup operacional de Qdrant/Postgres
observabilidade com alertas/runbooks/retenção
golden set de Recommendations/Briefing
versionamento histórico de recomendações/briefings
expansão ampla de Startup Discovery (mais hubs)
Firecrawl real (client ainda não implementado)
```

---

## 5. Roadmap futuro

### Próxima ordem recomendada

```txt
1. Validar Tavily real e calibrar ranking/allowlist do enriquecimento.
2. Criar golden set de Recommendations/Briefing (V5).
3. Medir precision@3 e taxa de falsos positivos das recomendações.
4. Expandir Startup Discovery para mais hubs sem virar crawler caro.
5. Só depois pensar em hardening de produção (auth, CI/CD, deploy, backup).
```

### Versões futuras por módulo (ainda não entregues)

```txt
Scraping            Firecrawl real como fallback pago
Ingestion           V2 limpeza textual forte, V3 dedup/versionamento, V5 reprocessamento/auditoria
RAG                 V5 completo (medir context_recall pós-BM25 via Ragas)
NVIDIA Knowledge    V3 metadados técnicos, V4 busca por caso de uso
Recommendations     V6 matriz de decisão por tecnologia, V7 feedback humano
Briefing            V5 ranking de oportunidades, V6
Orchestration       V3 retomada de jobs falhados (retry por etapa), V4 notificações
Startup Discovery   V2 (mais hubs, agendamento)
Frontend            auth real, tipos gerados de openapi.json
Observabilidade     métricas/alertas/retenção de produção
```

Cada roadmap detalhado vive em `docs/<modulo>/roadmap.md`.

---

## 6. Decisões de escopo já tomadas

```txt
Projeto é case/demo, não alvo de produção -> P2 (auth/CI-CD/deploy/backup) fora de escopo.
NVIDIA RAG Agent (V10) deliberadamente sem consumidor sub-tool — grounding RAG em
  recommendations/briefing já cobre a mesma necessidade por outro caminho.
"Sincronia Qdrant<->Postgres" redefinida: não há fluxo de edição (entidades
  write-once); o equivalente real implementado foi limpeza de vetores órfãos no re-scrape.
Dedup de startups com rapidfuzz (limiar 92 calibrado com 17 pares reais).
Rastreabilidade ponta a ponta (P3): toda recomendação e citação tem origem rastreável.
```

Documentos relacionados: `arquitetura_monolito_modular_workers.md`,
`comunicacao_entre_modulos.md`, `fluxo_total.md`, `stack_e_onde_e_usado.md`.
