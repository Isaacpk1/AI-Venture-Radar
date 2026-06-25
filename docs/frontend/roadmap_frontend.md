# Roadmap do Frontend

O frontend transforma o backend do NVIDIA Startup AI Radar em uma experiencia
operacional para analistas e, depois, em uma visao gerencial de oportunidades.

Stack definida:

```txt
Next.js + TypeScript + App Router + Tailwind CSS + TanStack Query
```

A arquitetura tecnica e as fronteiras com FastAPI estao em
`docs/frontend/nextjs_arquitetura.md`.

## Principio de evolucao

Cada versao deve entregar um fluxo completo utilizavel. O frontend nao executa
regras de negocio: envia comandos ao FastAPI, faz polling dos jobs e apresenta
o estado retornado pela API.

## Versoes planejadas

**Atualizado em 23/06/2026** apos sessao de brainstorm sobre o que agrega
valor real pro analista que vai usar isso (ver detalhe em cada versao
abaixo). V3/V4/V5 foram redesenhadas — mais foco em decisao e confianca,
menos em features que nao se pagam no escopo deste projeto (auth completa,
tempo real).

| Versao | Status | Objetivo |
|---|---|---|
| Frontend V1 | Entregue | Fundacao Next.js e jornada URL -> job |
| Frontend V2 | Entregue | Resultado da startup, evidencias, recomendacoes e briefing |
| Frontend V3 | Entregue (24/06/2026) | Confiabilidade, navegacao e decisao |
| Frontend V4 | Planejada (mais leve) | Indicadores de portfolio |
| Frontend V5 | Planejada (mais leve) | Revisao e colaboracao, sem auth completa |

## Frontend V1 — Fundacao e Jornada por URL

Objetivo:

```txt
usuario submete URL -> acompanha job -> recebe link para resultado
```

Entregaveis:

- criar `apps/web` com Next.js, TypeScript, App Router, Tailwind e ESLint;
- configurar `QueryClientProvider` e cliente HTTP compartilhado;
- criar BFF leve em `app/api/radar/` para encaminhar chamadas ao FastAPI;
- pagina inicial com explicacao curta do produto;
- pagina `/analyze` com formulario de URL e validacao de formato;
- `POST /url-ingestion/jobs` via BFF;
- pagina `/jobs/[jobId]` com linha do tempo de `pending`, `scraping`,
  `ingesting`, `embedding`, `analyzing`, `completed` e `failed`;
- polling a cada 3 segundos enquanto o job nao estiver terminal;
- estados visuais de carregamento, falha e conclusao;
- redirecionamento ou link para a startup quando `startup_id` estiver disponivel.

Criterio de pronto:

```txt
uma pessoa submete uma URL no navegador, acompanha a analise sem recarregar a
pagina e chega ao resultado ao fim do job.
```

Fora de escopo:

- autenticacao;
- listagem global de startups;
- edicao de perfil;
- painel BI;
- exportacao e revisao humana.

## Frontend V2 — Perfil e Resultado Executivo

Status:

```txt
entregue
```

Implementado em `apps/web/app/startups/[startupId]/page.tsx` e
`apps/web/features/startups/startup-details.tsx`, com BFFs internos para os
quatro recursos. As acoes de refazer extract/classify/recommendations/briefing
ficam para a proxima iteracao de operacao.

Objetivo:

```txt
startup_id -> perfil completo -> evidencias -> recomendacoes -> briefing
```

Entregaveis:

- pagina `/startups/[startupId]`;
- card de perfil: setor, pais, founders, funding, clientes e maturidade de IA;
- lista de evidencias com link para a fonte e nivel de confianca;
- lista de recomendacoes NVIDIA com score, palavras-chave e justificativa;
- visualizador seguro de briefing Markdown;
- acoes para refazer extract, classify, recommendations ou briefing quando os
  respectivos endpoints estiverem adequados ao fluxo;
- estados vazios para dados best-effort ainda nao preenchidos por LLM.

Criterio de pronto:

```txt
uma analise concluida pode ser compreendida integralmente sem consultar JSON ou
Swagger.
```

Dependencia:

```txt
Frontend V1 concluido.
```

## Frontend V3 — Confiabilidade, Navegacao e Decisao

**Status: Entregue (24/06/2026, em 2 fatias — ver `CLAUDE.md` "Frontend
module" para o detalhe completo de cada arquivo tocado).**

Objetivo:

```txt
operador encontra, filtra e confia no resultado, e sai com uma decisao
clara (engajar ou nao) — nao so com dados soltos na tela.
```

Entregaveis, em ordem de prioridade dentro da propria V3:

**1. Base de confiabilidade (pre-requisito, vem antes de tudo abaixo) — entregue:**
- Vitest + React Testing Library, cobrindo render dos componentes
  existentes (`StartupDetails`, `JobStatusPanel`, `UrlSubmissionForm`) —
  **correcao em 23/06/2026**: a afirmacao anterior de "bug real confirmado
  de Rules of Hooks" nao se confirmou lendo o arquivo na integra
  (`useMutation`/`useQueries` sao chamados corretamente, antes de qualquer
  `return` condicional); os testes seguem como fundacao de confiabilidade
  mesmo assim, protegendo contra esse tipo de regressao no futuro.

**2. Navegacao e historico — entregue:**
- **entregue em 24/06/2026 (1a fatia):** pagina `/startups`, cards de
  startups e listagem paginada via `GET /startups`, com busca e filtros
  interativos (setor, pais e maturidade de IA) ja inclusos nessa mesma
  fatia — o BFF em `app/api/radar/startups/route.ts` preserva o acesso
  ao FastAPI no servidor;
- **entregue em 24/06/2026 (2a fatia):** dashboard operacional com
  historico global de jobs — `UrlIngestionJobRepository.list_page()`
  novo (mirror exato do `list_page` de `startups`) + `GET
  /url-ingestion/jobs` paginado com filtros `status`/`source_type` +
  pagina `/jobs` (`features/jobs/job-history.tsx`);
- **entregue em 24/06/2026:** home (`/`) menos estatica — mostra o numero
  real de startups analisadas via `GET /startups?page_size=1` (so o
  `total`), trocando o texto fixo anterior;
- apresentacao de erros/loading/empty state consistente — ja existia nos
  componentes anteriores (`StartupPortfolio`, `JobStatusPanel`) e o
  `JobHistory` novo segue o mesmo padrao;
- "ultimo briefing gerado" na home **nao entrou nesta fatia** — ficou so
  a contagem de startups, que e' o dado mais barato de buscar sem
  endpoint agregado novo.

**3. Transparencia e confianca na decisao — entregue (24/06/2026):**
- badge consolidado de "fit"/pronto para contato —
  `computeFitBadge()` em `startup-details.tsx`, regra pura no frontend
  sobre dados que ja existem (`ai_maturity_level` + melhor score de
  recomendacao + briefing existir), sem chamada nova a API;
- evidencia clicavel por recomendacao — toggle "Ver evidencia" em cada
  card de recomendacao cruza `evidence_ids` com a lista de evidencias ja
  carregada e mostra o link de origem; `matched_keywords` exibidos como
  chips;
- achado real durante a implementacao (nao estava no escopo original
  deste bloco): o campo `customers` da `Startup` existia na API desde a
  Frontend V2 mas nunca era renderizado em `startup-details.tsx` —
  corrigido junto, mesmo arquivo;
- sinalizacao de campos incompletos como "Nao informado" — ja existia
  desde a V2 (`Field` component); confirmado que cobre `founders`/
  `funding_stage`, e `customers` passou a ter a mesma cobertura ao ser
  adicionado.

**4. Chatbot sobre a base de conhecimento NVIDIA — entregue (24/06/2026):**
- `features/knowledge/nvidia-chat.tsx` + pagina `/knowledge` — so UI,
  como previsto: `/rag/answer` ja existia (RAG V2), chamado via BFF novo
  `app/api/radar/rag/answer/route.ts` com `source_type=nvidia_knowledge`;
  mostra resposta + citacoes (link clicavel por citacao);
- chat sobre uma startup especifica continua de fora, como decidido —
  ainda exigiria filtro por `startup_id` em `rag/application/ports.py`,
  trabalho de backend nao incluido nesta entrega.

**5. Exportacao do briefing — entregue (24/06/2026), com 1 mudanca de
tecnologia em relacao ao planejado:**
- exportar PDF preservando citacoes — **decisao tecnica tomada durante a
  implementacao**: em vez de `weasyprint` + Jinja2 (planejado
  originalmente), usado **Playwright + Jinja2 + `markdown`**.
  `weasyprint` exige bibliotecas nativas (Pango/Cairo/GTK) com risco real
  de instalacao no Windows (ambiente deste projeto); `playwright` ja e'
  dependencia do projeto (Scraping V4) e ja funciona comprovadamente
  aqui. Ver `docs/briefing/briefing_v3_export_pdf.md` para o detalhe
  completo da entrega no modulo `briefing`;
- "HTML" como formato alternativo (mencionado no objetivo original) nao
  foi entregue separadamente — o Markdown ja e' visualizavel na propria
  tela da startup, e' so o PDF que precisava de um motor de renderizacao
  novo.

Validado end-to-end via `httpx.AsyncClient` contra a app real (alem dos
testes automatizados): criar startup -> recommendations -> briefing ->
`GET /url-ingestion/jobs` -> `GET /briefings/{id}/export` (PDF real,
28KB, `%PDF-1.4`) -> `POST /rag/answer`. `next build` e `tsc --noEmit`
sem erro. Validacao visual em navegador real ficou pendente nesta sessao
— o WSL deste ambiente nao alcanca processos Python/Node do lado Windows
pela rede (confirmado: o processo responde 200 do lado Windows via
`curl.exe`, so a travessia WSL->Windows falha; mesma categoria do
problema de DNS intermitente ja registrado no NVIDIA Knowledge V2).

**Extensao feita em 24/06/2026 — fechamento do P3** (diferencial do case
decidido: rastreabilidade ponta a ponta, ver
`docs/decisoes_pendentes.md`): a frase acima ("o Markdown ja e'
visualizavel") nao era verdade ainda na entrega original do bloco 5 —
`briefing.content` era mostrado num `<pre>` (texto cru) e
`recommendation.justification` num `<p>` simples, nenhum link Markdown
ficava clicavel fora do PDF. Corrigido com `MarkdownContent`
(`components/markdown-content.tsx`, novo, `react-markdown`+`remark-gfm`)
reusado em 3 lugares: briefing, justificativa de cada recomendacao
(`RecommendationCard`) e resposta do chatbot (`NvidiaChat`).
Dependencias novas: `react-markdown@^10`, `remark-gfm@^4` (JS puro, sem
risco de instalacao nativa). Testes: 23 -> 25 (+2, link Markdown
clicavel).

Criterio de pronto:

```txt
um analista localiza uma startup ou job anterior, confia no resultado sem
abrir o banco/Swagger, e sai da tela com uma decisao clara — nao so com
dados soltos.
```

Atingido.

## Frontend V4 — Indicadores de Portfolio (redesenhada, mais leve)

Objetivo:

```txt
dados de varias startups -> 2 indicadores simples que vendem a historia
de "ferramenta de triagem pro NVIDIA Inception", nao analise isolada.
```

Entregaveis (deliberadamente mais magro que o desenho original — "ranking
de oportunidades" completo so entra se houver volume real de startups que
justifique):

- grafico de distribuicao AI-native / AI-enabled / Non-AI;
- grafico de tecnologias NVIDIA mais recomendadas (top 5);
- comparacao lado a lado de 2-3 startups (maturidade, melhor recomendacao,
  score) — ideia da sessao de brainstorm, ajuda a decidir entre varias
  candidatas mais rapido que abrir uma de cada vez;
- fila de analises em lote: acompanhar progresso de varias URLs enviadas
  de uma vez, em vez de repetir o fluxo individual do V1;
- endpoints agregados especificos no backend (`GROUP BY ai_maturity_level`,
  `GROUP BY technology_name`) — o frontend nao deve calcular metricas
  lendo todas as entidades individualmente.

Criterio de pronto:

```txt
uma pessoa de negocio entende a distribuicao do portfolio e compara
candidatas sem abrir cada analise individual.
```

## Frontend V5 — Revisao e Colaboracao (redesenhada, sem auth completa)

Objetivo:

```txt
resultado passa por uma revisao registrada e pode ser compartilhado — sem
pagar o custo de autenticacao completa, que nao se justifica no escopo
deste projeto.
```

Entregaveis:

- revisao humana simples de recommendations/briefings: aprovar/rejeitar,
  comentarios e trilha de auditoria, **sem login/sessao real** (controle
  de acesso completo fica fora de escopo — ver P2 de
  `docs/roadmap_produto_final.md`, que ja trata auth como prontidao de
  producao, separada disto);
- retomada de `agent_runs` em `waiting_human_review`;
- notificacoes de conclusao continuam via polling (mesmo padrao do V1) —
  WebSocket/SSE seria over-engineering pro volume de uso deste projeto.

Criterio de pronto:

```txt
o resultado passa por revisao rastreavel e pode ser compartilhado com o
time responsavel, sem exigir infraestrutura de autenticacao.
```

---

**Fora do escopo deste roadmap, discutido e deliberadamente adiado:** uma
base de startups que se atualiza sozinha via scraping periodico/descoberta
de novas startups (sem URL manual) — ideia valida, mas e' uma decisao de
produto/custo maior (de onde vem a URL nova?) que vai ser tratada em
documento separado depois de fechar este roadmap de frontend.

## Ordem recomendada de implementacao

```txt
V1 -> V2 -> V3 -> V4 -> V5
```

V1 e V2 formam o primeiro MVP visual. V3 (redesenhada) era a que mais
importava antes de existir: sem ela corrigida e testada, qualquer coisa
nova construida em cima seria arriscada, e era onde moravam as ideias de
maior valor por menor custo (badge de fit, evidencia clicavel, chatbot
reusando `/rag/answer`) — **entregue por completo em 24/06/2026**. V4
(mais leve) e' o proximo: cria os 2 indicadores que vendem a historia de
portfolio. V5 (mais leve) entra por ultimo porque depende menos de codigo
novo e mais de uma decisao consciente de nao pagar o custo de
autenticacao completa agora.

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

Atualizado em 23/06/2026, reconferido em 24/06/2026: Vitest + React
Testing Library estao configurados, com 14 testes para
`UrlSubmissionForm`, `JobStatusPanel`, `StartupDetails` e
`StartupPortfolio`.
**Correcao em 23/06/2026:** este documento (e outros) afirmava um "bug real
confirmado de Rules of Hooks" em `StartupDetails`; lendo o arquivo na
integra agora, isso nao se confirma — os hooks sao chamados corretamente,
antes de qualquer `return` condicional. Mantendo a fundacao de testes
mesmo assim: a cobertura inicial protege os componentes existentes contra
esse tipo de regressao; rotas BFF e os fluxos futuros ainda precisam de
cobertura adicional.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| Cobertura inicial de frontend | `Vitest` + `React Testing Library` (compativel com React 19; mais rapido que Jest, sem Babel extra com Next.js) | Em evolucao | 14 testes de render e interacao para `StartupDetails`, `JobStatusPanel`, `UrlSubmissionForm` e `StartupPortfolio`; ampliar para BFF e filtros |
| Sem Prettier — so ESLint configurado, formatacao manual | `prettier` + `eslint-config-prettier` (libs padrao do ecossistema Next.js, zero infra nova) | Qualidade de codigo, baixo risco | Trivial |

Nao adotar um framework de teste e2e pesado (Playwright/Cypress) ainda: o
ganho imediato e' cobrir render/hooks dos componentes existentes, nao
fluxos de navegador completos — e2e fica melhor
posicionado junto da V3 (paginas de listagem/historico), quando houver mais
fluxo para cobrir.

**Para os 2 graficos da V4 — DECIDIDO em 23/06/2026**
(`docs/decisoes_pendentes.md`, secao 5): `recharts` — lib leve, comum no
ecossistema React/Next.js, evita reescrever SVG a mao pra so 2 graficos
simples (pizza de maturidade de IA, barra de top tecnologias). Decisao
fechada, nao SVG puro.

**Para o chatbot da V3:** nenhuma tecnologia nova — reusa `/rag/answer`
que ja existe (`rag` V4, com citacoes). So precisa de UI de chat no
frontend.
