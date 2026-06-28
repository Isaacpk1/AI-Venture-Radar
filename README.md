# NVIDIA Startup AI Radar

Plataforma para transformar fontes publicas sobre startups em evidencias rastreaveis, perfil estruturado, recomendacoes de tecnologias NVIDIA e briefing executivo.

## Estado do produto

O backend modular e o MVP visual estao funcionais e cobertos por testes. O produto ja cobre a jornada ponta a ponta, dashboard de portfolio e descoberta inicial de startups em hubs publicos. O que permanece fora ou alem do demo e hardening de auth, hardening de producao e enriquecimento automatico quando a primeira fonte e fraca.

Fluxo entregue:

```txt
URL -> scraping -> ingestion -> embeddings -> criar/associar startup
-> extract -> classify -> recommendations -> briefing -> frontend
```

Evolucao alvo:

```txt
startup discovery expandido -> revisao humana simples entregue
-> enriquecimento por busca -> hardening de producao (fora de escopo demo)
```

## Inicio rapido de desenvolvimento

1. Copie `.env.example` para `.env` e informe as chaves necessarias.
2. Suba Postgres, Redis, Qdrant e Langfuse com `docker compose -f infra/docker-compose.yml up -d`.
3. Aplique as migrations: `alembic upgrade head`.
4. Inicie a API e os workers descritos em `CLAUDE.md`.
5. Inicie o frontend em `apps/web` com `npm run dev`.

O compose atual disponibiliza as dependencias de infraestrutura. A API, os workers e o frontend ainda precisam ser executados localmente; a dockerizacao completa e parte do escopo de producao, hoje deliberadamente fora do demo.

## Documentacao

O indice e o estado atual ficam em `docs/README.md` e `docs/estado_atual_do_projeto.md`.
