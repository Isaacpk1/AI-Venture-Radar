# Frontend — Arquitetura Next.js

Atualizado em 23/06/2026. Este documento define como iniciar o frontend do
NVIDIA Startup AI Radar sem duplicar regras do backend FastAPI.

## 1. Estagio atual do produto

O backend esta pronto para receber uma interface:

```txt
URL -> scraping -> ingestion -> embeddings -> startup -> evidencia
-> extract/classify -> recommendations -> briefing
```

Esse fluxo e assíncrono e ja retorna um `UrlIngestionJob` consultavel em
`GET /url-ingestion/jobs/{id}`. Quando termina, a resposta inclui `startup_id`,
`recommendation_count` e `briefing_id`. A primeira tela deve usar esse contrato
em vez de conhecer workers, Redis ou Dramatiq.

Validacao atual: 457 testes do backend passam. Nao ha aplicacao Next.js criada
ainda; `packages/` esta vazio. A proposta abaixo cria o frontend em `apps/web`,
alinhado ao layout ja previsto em `CLAUDE.md`.

## 2. Escolha de arquitetura

Usar:

```txt
Next.js + TypeScript + App Router + Tailwind CSS + TanStack Query
```

- **Next.js App Router** organiza paginas por pastas em `app/`. Um `page.tsx`
  vira uma rota, por exemplo `app/jobs/[jobId]/page.tsx` vira
  `/jobs/:jobId`.
- **Server Components** sao o padrao: renderizam no servidor e leem dados que
  nao precisam de interacao no navegador.
- **Client Components** usam `'use client'` e ficam restritos ao que interage:
  formulario, botoes, polling de job, filtros e modais.
- **TanStack Query** administra somente estado remoto no navegador: cache,
  carregamento, erro, refetch e polling. Ele nao substitui estado visual local.
- **Tailwind** cuida da apresentacao; componentes devem encapsular padroes
  repetidos de UI, sem misturar chamadas HTTP dentro deles.

## 3. Regra de fronteira: Next nao reimplementa o backend

O FastAPI continua sendo a fonte de verdade para regras de negocio, jobs,
persistencia e autorizacao futura. O frontend apenas envia comandos e apresenta
os dados recebidos.

```txt
Browser
  -> Next.js (paginas, componentes e BFF leve)
  -> FastAPI (contratos HTTP e regras de negocio)
  -> PostgreSQL / Redis / Qdrant / workers
```

O browser nunca acessa Redis, Qdrant, workers ou banco diretamente.

### Por que usar um BFF leve no Next

Enquanto FastAPI ainda nao possui CORS, autenticacao e sessao, os Client
Components devem chamar rotas internas do Next (`/api/radar/...`). Essas rotas
apenas encaminham a requisicao para o FastAPI; nao devem conter regra de
negocio, nem manter uma segunda representacao de dados.

Beneficios:

- o endereco do FastAPI fica em `RADAR_API_URL`, sem ser exposto ao browser;
- evita depender de CORS durante o MVP;
- cria um ponto unico para cookies/sessao quando auth for adicionada;
- facilita trocar URL interna no deploy.

Server Components tambem podem usar o cliente HTTP compartilhado diretamente,
pois executam no servidor Next. No navegador, usar sempre o BFF.

## 4. Estrutura de diretorios proposta

```txt
apps/web/
  app/
    layout.tsx                    # shell global: navegacao, providers, estilos
    page.tsx                      # dashboard inicial
    analyze/page.tsx              # formulario para submeter URL
    jobs/[jobId]/page.tsx         # acompanhamento do pipeline
    startups/[startupId]/page.tsx # perfil, evidencias, recomendacoes e briefing
    api/radar/
      url-ingestion-jobs/route.ts
      url-ingestion-jobs/[jobId]/route.ts
      startups/[startupId]/route.ts
      startups/[startupId]/evidences/route.ts
      recommendations/route.ts
      briefings/route.ts
  components/
    ui/                           # Button, Card, Badge, Skeleton, EmptyState
    analysis/                     # UrlSubmissionForm, JobTimeline, JobResult
    startup/                      # StartupProfile, EvidenceList, RecommendationList
    briefing/                     # BriefingViewer
  features/
    analysis/                     # hooks, query keys e tipos do fluxo URL
    startups/                     # hooks e mapeadores do perfil
  lib/
    api/
      radar-server.ts             # cliente usado por Server Components/BFF
      radar-types.ts              # tipos de resposta FastAPI
    env.ts                        # valida RADAR_API_URL
  providers/
    query-provider.tsx            # QueryClientProvider
  styles/
  public/
```

`components/` nao conhece URLs do FastAPI. Chamadas HTTP e tipos vivem em
`features/` e `lib/api/`; assim, trocar um endpoint nao obriga a alterar a UI.

## 5. Páginas do MVP

| Rota | Objetivo | Fonte de dados |
|---|---|---|
| `/` | Explicar o produto e direcionar para uma analise | Estatica inicialmente |
| `/analyze` | Receber uma URL e iniciar o job | `POST /url-ingestion/jobs` |
| `/jobs/[jobId]` | Mostrar linha do tempo, progresso, erro ou resultado | `GET /url-ingestion/jobs/{id}` por polling |
| `/startups/[startupId]` | Mostrar perfil, evidencias, recomendacoes e briefing | endpoints de startups, recommendations e briefings |

Nao iniciar por uma tela de dashboard global: ainda faltam endpoints paginados
para listar startups e jobs. O fluxo por URL ja tem um contrato completo e e o
melhor primeiro corte vertical.

## 6. Fluxo de tela principal

```txt
Usuario informa URL em /analyze
  -> POST /api/radar/url-ingestion-jobs
  -> Next encaminha para POST /url-ingestion/jobs
  -> redireciona para /jobs/{jobId}
  -> TanStack Query consulta GET /api/radar/url-ingestion-jobs/{jobId}
       a cada 3 segundos enquanto status nao e completed/failed
  -> completed com startup_id
       -> link para /startups/{startupId}
  -> failed
       -> mostra error_message e acao para tentar nova submissao
```

Estados que a `JobTimeline` deve conhecer: `pending`, `scraping`,
`ingesting`, `embedding`, `analyzing`, `completed` e `failed`. A interface nao
deve inferir progresso pelo tempo; ela deve apenas apresentar o estado vindo da
API e parar o polling em estados terminais.

## 7. Contratos iniciais do frontend

O primeiro conjunto de funcoes do cliente deve cobrir somente:

```ts
createUrlIngestionJob(input: { url: string; startupId?: string })
getUrlIngestionJob(jobId: string)
getStartup(startupId: string)
getStartupEvidences(startupId: string)
listRecommendations(startupId: string)
listBriefings(startupId: string)
```

Tipos devem espelhar as respostas Pydantic da API. A evolucao desejada e gerar
tipos a partir de `openapi.json` do FastAPI, em vez de manter interfaces
duplicadas manualmente. Isso pode entrar depois do primeiro fluxo visual estar
funcional.

## 8. Estado e polling com TanStack Query

Chaves recomendadas:

```txt
["url-ingestion-job", jobId]
["startup", startupId]
["startup-evidences", startupId]
["recommendations", startupId]
["briefings", startupId]
```

Para o job, usar `refetchInterval` somente enquanto ele nao for terminal. Ao
receber `completed`, invalidar as chaves da startup e navegar ou liberar o link
para o resultado. Erros HTTP devem virar uma mensagem compreensivel, mas a tela
deve preservar `error_message` retornado pelo backend para suporte.

## 9. O que o frontend nao deve fazer

- nao chamar `/url-ingestion/jobs/{id}/advance`: o worker ja avanca o job;
- nao repetir validacao de negocio de scraping, classificacao ou recomendacao;
- nao colocar `RADAR_API_URL` ou chaves de servicos em variaveis `NEXT_PUBLIC_*`;
- nao usar polling para estados que ja sao terminais;
- nao assumir que extract/classify sempre terao dados: sao best-effort quando
  Gemini nao esta configurado;
- nao criar uma API GraphQL, camada ORM ou banco proprio para o frontend.

## 10. Variaveis de ambiente

```env
# Somente servidor Next; nunca prefixar com NEXT_PUBLIC_
RADAR_API_URL=http://127.0.0.1:8000
```

Quando houver deploy com containers, apontar para o hostname interno da API.
Autenticacao futura adicionara segredos de sessao no Next e tokens/credenciais
verificados pelo FastAPI; isso nao faz parte do primeiro corte visual.

## 11. Sequencia de implementacao

1. Criar `apps/web` com TypeScript, App Router, Tailwind e ESLint.
2. Criar `lib/api`, tipos de `UrlIngestionJob` e as duas rotas BFF do job.
3. Implementar `/analyze` e `/jobs/[jobId]`, incluindo estados vazio,
   carregando, processando, concluido e falho.
4. Implementar `/startups/[startupId]` com cards de perfil, evidencias,
   recomendacoes e briefing Markdown.
5. Extrair componentes visuais reutilizaveis e criar testes dos fluxos.
6. So depois, adicionar dashboard/listagens quando o backend fornecer filtros
   e paginacao adequados.

## 12. Testes do frontend

- testes unitarios para mapeadores, cliente HTTP e componentes de estado;
- testes de integracao para `UrlSubmissionForm` e `JobTimeline`, simulando o
  BFF;
- um teste end-to-end do caminho URL -> job concluido usando respostas
  controladas; integracao com infraestrutura real fica em uma etapa separada.

## 13. Decisao para comecar

O primeiro incremento recomendado e pequeno e demonstravel: formulario de URL
mais acompanhamento de job. Ele exercita o principal diferencial do produto —
uma analise rastreavel de ponta a ponta — e estabelece os providers, cliente
HTTP, BFF e padrao de polling que as demais telas vao reutilizar.
