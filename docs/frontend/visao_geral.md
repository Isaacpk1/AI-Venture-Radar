# Módulo Frontend — Visão Geral

## 1. Importância

O `frontend` opera o pipeline e apresenta o resultado para o usuário de negócio
ou técnico. Ele não executa regra de negócio: envia comandos ao FastAPI por um
BFF leve (`/api/radar`), faz polling dos jobs e apresenta o estado retornado pela
API. O FastAPI continua sendo a fonte da verdade; o browser nunca acessa
Redis/Qdrant/workers/banco diretamente.

## 2. Fluxo de tela principal

```txt
Usuário informa URL em /analyze
  -> POST /api/radar/url-ingestion-jobs (BFF) -> POST /url-ingestion/jobs (FastAPI)
  -> redireciona para /jobs/{jobId}
  -> TanStack Query consulta o job a cada 3s enquanto não for terminal
  -> completed -> link para /startups/{startupId}
  -> failed    -> mostra error_message e ação para nova submissão
```

Telas: `/`, `/analyze`, `/jobs`, `/jobs/[jobId]`, `/startups`,
`/startups/[startupId]`, `/knowledge`, `/dashboard`.

## 3. Estrutura de pastas

```txt
apps/web/
  app/              páginas (App Router) + api/radar/ (BFF leve)
  components/       ui/, markdown-content.tsx
  features/         analysis/, startups/, jobs/, knowledge/, dashboard/ (hooks/tipos/telas)
  lib/api/          radar-server.ts (cliente BFF), radar-client.ts, radar-types.ts, env.ts
  providers/        query-provider.tsx
  styles/ public/
```

`components/` não conhece URLs do FastAPI; chamadas HTTP e tipos vivem em
`features/` e `lib/api/`.

## 4. Stack

```txt
Next.js (App Router)    páginas + BFF
React 19 + TypeScript   componentes e tipos
TanStack Query          polling/cache/retry de estado remoto
Tailwind CSS            estilo
react-markdown + remark-gfm   briefing/justificativa/chat com links clicáveis
SVG/HTML em React       gráficos do dashboard (sem chart lib)
Vitest + Testing Library  32 testes
```

## 5. Histórico de versões

| Versão | Status | Entrega |
|---|---|---|
| V1 | Entregue | Fundação Next.js e jornada URL -> job |
| V2 | Entregue | Resultado da startup: evidências, recomendações, briefing |
| V3 | Entregue | Portfólio paginado, histórico de jobs, badge de fit, evidência clicável, chatbot, export PDF |
| V4 | Entregue | Dashboard (gráficos), comparação de startups, fila em lote |
| V5 | Entregue | Revisão humana simples (pending/approved/rejected) sem auth completa |

**Versão atual: V5.** Detalhes em `versoes/`; futuro (auth real, tipos de
openapi.json) em `roadmap.md`.
