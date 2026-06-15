# Skill ai-venture-radar-docs

Este documento explica como criar e usar uma skill do Codex para sempre lembrar de ler a documentacao do projeto antes de mexer na arquitetura, nos modulos, nos workers ou nos agentes.

## 1. O que e uma skill?

Uma skill e um pequeno conjunto de instrucoes que o Codex pode carregar quando um assunto especifico aparece.

Neste caso, queremos uma skill para o projeto:

```txt
AI-Venture-Radar
```

Objetivo: 

```txt
antes de mexer no codigo, ler os documentos certos do projeto
```

## 2. Onde a skill deve ficar?

A skill deve ficar fora do projeto, na pasta do Codex:

```txt
C:\Users\Inteli\.codex\skills\ai-venture-radar-docs\SKILL.md
```

Hoje essa skill ainda nao existe.

Para ver as skills instaladas:

```powershell
Get-ChildItem C:\Users\Inteli\.codex\skills -Force
```

Para abrir a pasta no Explorer:

```powershell
explorer C:\Users\Inteli\.codex\skills
```

## 3. Conteudo da skill

O arquivo `SKILL.md` deve ter este conteudo:

```md
---
name: ai-venture-radar-docs
description: Use when working on the AI-Venture-Radar project, especially for architecture, modules, workers, scraping, agents, persistence, queues, LangGraph, or code changes. Always read the relevant docs before proposing or editing code.
---

# AI Venture Radar Docs First

Before changing code, inspect the project documentation.

## Required First Reads

For architecture or module boundaries, read:

- docs/arquitetura_global_monolito_modular_workers.md
- docs/validacao_arquitetural_modulos_workers.md
- docs/validacao_mensagens_interacoes_modulos.md
- docs/roadmap_proximos_passos.md

For scraping work, read:

- docs/scraping/modulo_scraping_atualizado.md
- the latest docs/scraping/scraper_v*.md relevant to the task

For agents work, read:

- docs/agentes/roadmap_agentes.md
- latest docs/agentes/agents_v*.md relevant to the task
- docs/agents/modulo_agents_arquitetura.md when architecture is involved

## Rules

- Validate docs against code before editing.
- Modules own business logic.
- Workers only receive identifiers and call module use cases.
- Queues should transport small messages, preferably IDs.
- Shared infrastructure belongs in apps/api/src/shared.
- Do not make one module import another module's internal infrastructure.
```

## 4. Como usar depois de criada

Em uma conversa nova, voce pode dizer:

```txt
Use a skill ai-venture-radar-docs e valide a arquitetura
```

Ou:

```txt
Use ai-venture-radar-docs e vamos mexer nos agents
```

Isso aumenta muito a chance do Codex carregar essas instrucoes e ler os documentos certos antes de alterar o projeto.

## 5. Observacao importante

A skill nao fica dentro de `docs` porque o Codex descobre skills pela pasta:

```txt
C:\Users\Inteli\.codex\skills
```

Este documento em `docs` e apenas uma referencia visual dentro do projeto.

Para a skill funcionar de verdade, o arquivo `SKILL.md` precisa existir na pasta `.codex\skills`.
