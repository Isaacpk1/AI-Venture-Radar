# Roadmap para Fechar o Produto

Atualizado em 23/06/2026 a partir da revisao cruzada de codigo, testes e
documentacao. Este documento prioriza o que falta para transformar o backend
atual em um produto utilizavel, operavel e apresentavel.

## Diagnostico resumido

O backend possui scraping, ingestao, embeddings, RAG, catalogo NVIDIA,
startups, recomendacoes, briefings, workers e oito agentes LangGraph. A suite
local tem 476 testes coletados (`pytest --collect-only`, 2026-06-23). A
jornada unica da URL ate o briefing (P0 #1) ja esta fechada. O frontend
(P0 #2) **nao falta mais por completo** — Frontend V1 e V2 ja estao
entregues e commitados (`docs/frontend/roadmap_frontend.md`), cobrindo
submissao de URL, acompanhamento de job e o resultado completo da startup
(evidencias, recomendacoes, briefing). O que resta do P0 #2 e'
especificamente historico/listagem paginada (Frontend V3) e revisao
humana/auth (Frontend V5) — ver secao 2 abaixo.

## P0 — Jornada funcional de ponta a ponta

### 1. Fechar Orchestration V2 — ENTREGUE

```txt
entregue
```

Implementado (ver `docs/orchestration/orchestration_v2_jornada_completa.md`):

- criar ou associar uma `Startup` ao concluir a ingestao de uma URL — entregue;
- anexar evidencias rastreaveis ao perfil — entregue;
- executar extract e classify — entregue (best-effort, nao bloqueia o
  restante quando o servico de LLM nao esta configurado);
- gerar recommendations e briefing — entregue;
- persistir o estado, IDs downstream e erro de cada etapa — entregue;
- expor consulta agregada do job para polling do frontend — entregue
  (`startup_id`/`recommendation_count`/`briefing_id` em
  `GET /url-ingestion/jobs/{id}`);
- garantir idempotencia e retomada segura — entregue (guardas contra
  reentrega-por-crash do Dramatiq).

**Pronto quando:** uma URL de startup produz briefing e recomendacoes sem
operacao manual entre as etapas. Atingido.

### 2. Frontend operacional — PARCIALMENTE ENTREGUE (V1+V2)

Arquitetura definida em `docs/frontend/nextjs_arquitetura.md`.
Roadmap versionado em `docs/frontend/roadmap_frontend.md`.

Telas minimas:

- submissao de URL e criacao manual de startup — **entregue (V1)**;
- acompanhamento de pipeline e erros — **entregue (V1)**, pagina
  `/jobs/[jobId]` com timeline e polling;
- evidencias, perfil estruturado e classificacao — **entregue (V2)**,
  pagina `/startups/[startupId]`;
- recomendacoes e briefing com citacoes — **entregue (V2)**;
- listagem/historico paginado de startups e jobs — **falta (Frontend V3)**;
- tela de revisao humana e retomada de casos pendentes — **falta
  (Frontend V5)**, depende de autenticacao.

Gap conhecido fora do roadmap de telas: `apps/web` ainda nao tem nenhum
teste automatizado, e um teste manual ja encontrou um bug real de Rules of
Hooks em `StartupDetails` que trava a pagina de resultado — ver a secao de
tecnologias candidatas em `docs/frontend/roadmap_frontend.md`.

O backend deve receber endpoints de listagem, busca e paginacao consistentes,
incluindo startups e jobs de URL, para suportar a tela de historico (V3).

## P1 — Qualidade da decisao

### 3. Completar NVIDIA Knowledge V2 — ENTREGUE (23/06/2026)

```txt
entregue
```

P0+P1+P2 completo: 20/20 fontes processadas, 17/20 com conteudo
recuperavel via `/rag/search`. Restam 3 gaps sem fix de codigo possivel
agora (DNS intermitente Windows-side em 2 fontes, Firecrawl necessario
para a terceira — ver `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md`,
"Tecnologias candidatas"). Nao bloqueiam mais o restante do P1.

### 4. Recommendations V2/V4

- buscar contexto NVIDIA via RAG com citacoes;
- aprofundar o uso de `ai_maturity_level` no score (bonus deterministico inicial entregue);
- adicionar prioridade, confianca, complexidade, proxima acao e trade-offs;
- separar justificativa de negocio da justificativa tecnica;
- integrar Recommendation Agent V11 ao caminho principal quando aplicavel.

### 5. Briefing e revisao

- integrar Briefing Agent V12 ao fluxo principal quando aplicavel;
- exportar HTML/PDF preservando citacoes;
- aprovar/rejeitar, comentar e manter historico de revisao;
- ranquear oportunidades e gerar visao de lote.

## P2 — Prontidao de producao

- autenticacao, autorizacao e isolamento por usuario/organizacao;
- CORS configuravel, rate limiting e controles de abuso;
- logs estruturados, correlation IDs, metricas, tracing, alertas e monitoramento
  de custo/latencia de LLM;
- CI com testes, verificacao de migrations e analise estatica;
- Dockerfiles e compose/manifestos para API e todos os workers;
- backups, retencao de dados, limpeza de checkpoints e plano de rollback;
- documentacao de operacao, variaveis de ambiente e runbooks.

## P3 — Apresentacao do case

- escolher e documentar o diferencial: rastreabilidade ponta a ponta, hibrido
  deterministico/agente por excecao e cobertura do NVIDIA Inception sao os
  candidatos mais fortes;
- preparar demonstracao com uma startup real e fontes NVIDIA recuperaveis;
- definir metricas de valor: tempo ate briefing, cobertura de evidencias,
  qualidade das recomendacoes e taxa de revisao/aprovacao.

## Ordem de implementacao recomendada (auditoria 23/06/2026)

Cruza a auditoria de regras arquiteturais
(`docs/validacao_arquitetural_modulos_workers.md`), o roadmap de qualidade
do pipeline (`docs/roadmap_evolucao_tecnica_mvp.md`) e as secoes
"Tecnologias candidatas" de cada `docs/<modulo>/roadmap_<modulo>.md`. Nao
repete o detalhe de cada item — so a sequencia e o motivo da ordem.

```txt
1. Fix arquitetural rag->embeddings
   (Fase 5 de roadmap_evolucao_tecnica_mvp.md). Primeiro porque e risco
   zero (refatoracao de fronteira, sem mudar comportamento) e corrige um
   drift que a propria documentacao do projeto ja apontava.

2. Itens triviais/baixo esforco das secoes "Tecnologias candidatas"
   (COHERE_RERANK_MODEL configuravel - Fase 4 da evolucao tecnica; cache
   por content_hash em scraping/ingestion/embeddings). Mesma logica: baixo
   risco, ganho imediato de custo/qualidade, nenhuma decisao de
   arquitetura nova.

3. P1 #4/#5 (Recommendation Agent V11 e Briefing Agent V12 no caminho
   principal) + rapidfuzz para dedup em startups (V4). Esforco medio,
   mas desbloqueia capacidade ja construida e testada (os agentes existem
   desde Agents V11/V12) em vez de criar algo novo.

4. Chain de enriquecimento por busca (Search Planner Agent + client de
   busca novo, ver docs/agents/roadmap_agentes.md e
   docs/orchestration/roadmap_orchestration.md). Depois dos itens 1-3
   porque e a unica peca desta lista que exige decidir uma dependencia
   externa nova (API de busca, recomendacao: Tavily) e tem o maior custo
   recorrente por execucao (LLM + busca + scraping + LLM de novo).

5. BM25/pg_search (Fase 3 da evolucao tecnica) — so entra se o numero
   medido de `context_recall` (hoje 0.67) realmente justificar a troca;
   nao tem ordem fixa em relacao aos itens 2-4, e' bloqueado por decisao
   de dados, nao por sequencia.

6. P2 (autenticacao, CORS, rate limiting, CI/CD, Dockerfiles, backups) e
   P3 (diferencial do case, demo) — inalterados, continuam por ultimo:
   dependem de o produto estar funcionalmente fechado primeiro.
```

---

## Pendencias de documentacao e release

- manter este roadmap como fonte de priorizacao;
- atualizar documentos historicos quando uma entrega alterar seu status;
- versionar e aplicar a migration `7d4f2a9c6e83` antes de deployar o codigo que
  usa `scraping_jobs.source_type`;
- manter o README raiz com o caminho de execucao atualizado.
