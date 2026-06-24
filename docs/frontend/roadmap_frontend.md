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
| Frontend V3 | Em andamento | Confiabilidade, navegacao e decisao |
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

Objetivo:

```txt
operador encontra, filtra e confia no resultado, e sai com uma decisao
clara (engajar ou nao) — nao so com dados soltos na tela.
```

Entregaveis, em ordem de prioridade dentro da propria V3:

**1. Base de confiabilidade (pre-requisito, vem antes de tudo abaixo):**
- Vitest + React Testing Library, cobrindo render dos componentes
  existentes (`StartupDetails`, `JobStatusPanel`, `UrlSubmissionForm`) —
  **correcao em 23/06/2026**: a afirmacao anterior de "bug real confirmado
  de Rules of Hooks" nao se confirmou lendo o arquivo na integra
  (`useMutation`/`useQueries` sao chamados corretamente, antes de qualquer
  `return` condicional); os testes seguem como fundacao de confiabilidade
  mesmo assim, protegendo contra esse tipo de regressao no futuro.

**2. Navegacao e historico:**
- **entregue em 24/06/2026:** pagina `/startups`, cards de startups e
  listagem paginada via `GET /startups`; o BFF em
  `app/api/radar/startups/route.ts` preserva o acesso ao FastAPI no servidor;
- busca e filtros interativos na pagina (setor, pais e maturidade de IA);
- filtros por status, data, setor, pais e maturidade de IA;
- dashboard operacional com jobs recentes e historico de analises;
- home menos estatica: mostrar numero real de startups analisadas/ultimo
  briefing gerado em vez de so texto fixo;
- apresentacao clara de erros recuperaveis e falhas terminais, com loading/
  empty/error state consistentes;
- endpoints paginados no backend quando os existentes nao cobrirem a tela.

**3. Transparencia e confianca na decisao (ideias da sessao de brainstorm):**
- badge consolidado de "fit"/pronto para contato — regra simples sobre
  dados que ja existem (`ai_maturity_level` + melhor score de recomendacao
  + briefing completo), em vez de o analista juntar tudo na cabeca;
- evidencia clicavel por recomendacao: expandir `matched_keywords` e
  `evidence_ids` ja existentes pra mostrar o trecho de origem, nao so a
  justificativa em texto;
- sinalizar (nao escconder) campos incompletos — `founders`/`funding`
  vazios porque a evidencia nao mencionou isso devem aparecer como "nao
  encontrado", nao em branco sem explicacao.

**4. Chatbot sobre a base de conhecimento NVIDIA:**
- backend ja pronto — `/rag/answer` filtrado por
  `source_type=nvidia_knowledge` ja faz pergunta -> evidencia -> resposta
  com citacoes; esta entrega e' so a UI de chat + mostrar as citacoes
  (reforca o diferencial de rastreabilidade do `roadmap_produto_final.md`
  P3);
- chat sobre uma startup especifica fica de fora aqui — exigiria adicionar
  filtro por `startup_id` em `rag/application/ports.py`
  (`LexicalSearchRepository`/`VectorRepository.search()` so filtram por
  `source_type` hoje), e' trabalho de backend, nao so frontend.

**5. Exportacao do briefing (movido de V5 — e' barato, encaixa direto no card):**
- exportar HTML/PDF preservando citacoes (backend: `weasyprint` + Jinja2,
  ver `docs/briefing/roadmap_briefing.md`).

Criterio de pronto:

```txt
um analista localiza uma startup ou job anterior, confia no resultado sem
abrir o banco/Swagger, e sai da tela com uma decisao clara — nao so com
dados soltos.
```

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

V1 e V2 formam o primeiro MVP visual. V3 (redesenhada) e' a que mais importa
agora: sem ela corrigida e testada, qualquer coisa nova construida em cima e'
arriscada, e e' onde moram as ideias de maior valor por menor custo (badge de
fit, evidencia clicavel, chatbot reusando `/rag/answer`). V4 (mais leve) cria
os 2 indicadores que vendem a historia de portfolio. V5 (mais leve) entra por
ultimo porque depende menos de codigo novo e mais de uma decisao consciente
de nao pagar o custo de autenticacao completa agora.

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

Atualizado em 23/06/2026: Vitest + React Testing Library estao configurados,
com 13 testes para `UrlSubmissionForm`, `JobStatusPanel`, `StartupDetails` e
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
| Cobertura inicial de frontend | `Vitest` + `React Testing Library` (compativel com React 19; mais rapido que Jest, sem Babel extra com Next.js) | Em evolucao | 13 testes de render e interacao para `StartupDetails`, `JobStatusPanel`, `UrlSubmissionForm` e `StartupPortfolio`; ampliar para BFF e filtros |
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
