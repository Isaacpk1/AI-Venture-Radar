# NVIDIA Startup AI Radar

Plataforma para transformar fontes publicas sobre startups em evidencias
rastreaveis, perfil estruturado, recomendacoes de tecnologias NVIDIA e briefing
executivo.

## Estado do produto

O backend modular e o primeiro MVP visual estao funcionais e cobertos por
testes. O produto final ainda esta em construcao: faltam historico de
analises, enriquecimento do motor de recomendacoes e requisitos de producao.

Fluxo entregue:

```txt
URL -> scraping -> ingestion -> embeddings -> criar/associar startup
-> extract -> classify -> recommendations -> briefing
```

Evolucao alvo:

```txt
historico/listagem -> revisao/exportacao -> hardening de producao
```

## Inicio rapido de desenvolvimento

1. Copie `.env.example` para `.env` e informe as chaves necessarias.
2. Suba Postgres, Redis e Qdrant com `docker compose -f infra/docker-compose.yml up -d`.
3. Aplique as migrations: `alembic upgrade head`.
4. Inicie a API e os workers descritos em `CLAUDE.md`.

O compose atual disponibiliza apenas as dependencias de infraestrutura. A API e
os workers ainda precisam ser executados localmente; a dockerizacao completa e
parte do roadmap de producao.

## Documentacao

O indice e o roadmap de produto ficam em `docs/README.md` e
`docs/roadmap_produto_final.md`.
