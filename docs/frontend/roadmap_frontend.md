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

| Versao | Status | Objetivo |
|---|---|---|
| Frontend V1 | Entregue | Fundacao Next.js e jornada URL -> job |
| Frontend V2 | Entregue | Resultado da startup, evidencias, recomendacoes e briefing |
| Frontend V3 | Planejada | Operacao e historico de analises |
| Frontend V4 | Planejada | Painel BI de oportunidades |
| Frontend V5 | Planejada | Revisao humana, auth e colaboracao |

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

## Frontend V3 — Operacao e Historico

Objetivo:

```txt
operador encontra, filtra e acompanha analises sem depender de links salvos.
```

Entregaveis:

- dashboard operacional com jobs recentes;
- busca e listagem paginada de startups;
- filtros por status, data, setor, pais e maturidade de IA;
- pagina de historico de analises por startup;
- apresentacao clara de erros recuperaveis e falhas terminais;
- telas de loading, empty state e error state consistentes;
- endpoints paginados no backend quando os existentes nao cobrirem a tela.

Criterio de pronto:

```txt
um analista consegue localizar uma startup ou job anterior e entender seu
estado sem acesso direto ao banco.
```

## Frontend V4 — BI e Portfólio de Oportunidades

Objetivo:

```txt
dados de varias startups -> indicadores e oportunidades priorizadas
```

Entregaveis:

- painel com total de startups, analises concluidas/falhas e tempo medio de
  processamento;
- distribuicao por setor, pais e maturidade de IA;
- tecnologias NVIDIA mais recomendadas;
- ranking de oportunidades e filtros de portfolio;
- visao de qualidade: cobertura de evidencias e taxa de recomendacoes;
- endpoints agregados especificos no backend; o frontend nao deve calcular
  metricas lendo todas as entidades individualmente.

Criterio de pronto:

```txt
uma pessoa de negocio entende o portfolio e identifica oportunidades sem abrir
cada analise individual.
```

## Frontend V5 — Revisao, Autenticacao e Colaboracao

Objetivo:

```txt
usuarios autenticados revisam resultados, deixam decisao registrada e exportam
materiais executivos.
```

Entregaveis:

- login, sessao e controle de acesso por usuario/organizacao;
- revisao humana de recommendations e briefings;
- aprovar/rejeitar, comentarios e trilha de auditoria;
- retomada de `agent_runs` em `waiting_human_review`;
- exportacao HTML/PDF do briefing;
- notificacoes de conclusao e falha;
- preferencia de polling ou notificacao em tempo real definida por caso de uso.

Criterio de pronto:

```txt
o resultado passa por revisao rastreavel e pode ser compartilhado de forma
segura com o time responsavel.
```

## Ordem recomendada de implementacao

```txt
V1 -> V2 -> V3 -> V4 -> V5
```

V1 e V2 formam o primeiro MVP visual. V3 melhora a operacao diaria. V4 cria a
camada de BI. V5 entra junto com os requisitos de autenticacao, revisao humana
e exportacao que tambem dependem de evolucoes no backend.
