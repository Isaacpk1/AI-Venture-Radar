# Roadmap dos Agentes

Esta pasta concentra a documentacao em portugues do modulo de agentes.

Documento de validacao arquitetural:

```txt
docs/validacao_arquitetural_modulos_workers.md
```

## Versoes

| Versao | Status | Documento |
| --- | --- | --- |
| Agents V1 | Implementado | `docs/agents/agents_v1_integracao_inicial.md` |
| Agents V2 | Implementado | `docs/agents/agents_v2_langgraph.md` |
| Agents V3 | Implementado | `docs/agents/agents_v3_search_planner.md` |
| Agents V3.5 | Implementado | `docs/agents/agents_v3_5_agent_worker_base.md` |
| Agents V4 | Implementado | `docs/agents/agents_v4_agent_runs_persistence.md` |
| Agents V5 | Implementado | `docs/agents/agents_v5_executar_grafos_pelo_agent_run.md` |
| Agents V6 | Implementado | `docs/agents/agents_v6_checkpoint_postgres.md` |
| Agents V7 | Implementado | `docs/agents/agents_v7_human_in_the_loop.md` |
| Agents V8 | Futuro | Extraction Agent |
| Agents V8 | Futuro | Startup Classifier Agent |
| Agents V9 | Futuro | NVIDIA Knowledge Agent |
| Agents V10 | Futuro | Recommendation Agent |
| Agents V11 | Futuro | Briefing Agent |

## Agentes Planejados

### Evidence Validation Agent

Valida se uma evidencia coletada pelo scraper deve ser aceita, rejeitada ou se precisa de mais fontes.

Status:

```txt
V1 com Gemini simples implementada
V2 com LangGraph e LangChain implementada
```

### Search Planner Agent

Planeja buscas quando uma evidencia nao for suficiente.

Status:

```txt
implementado na V3
```

### Scraper Coordination Agent

Coordena novas coletas chamando o modulo de scraping por contratos publicos.

### Agent Worker

Executa jobs de agentes fora da API usando Redis/Dramatiq.

Status:

```txt
base criada na V3.5
persistencia de agent_runs criada na V4
execucao real dos grafos pelo worker implementada na V5
```

### Extraction Agent

Extrai dados estruturados das evidencias aceitas.

### Startup Classifier Agent

Classifica startups por setor, tipo de IA, maturidade e aderencia tecnica.

### NVIDIA Knowledge Agent

Consulta a base RAG de conhecimento NVIDIA.

### Recommendation Agent

Recomenda tecnologias NVIDIA para uma startup com justificativa e evidencias.

### Briefing Agent

Gera uma analise final clara para negocio.

## Regra Principal

Um agente coordena fluxo. Ele nao deve concentrar toda a regra de negocio.

O padrao correto e:

```txt
agent -> contratos publicos -> services/use cases/tools -> resultado estruturado
```

O proximo passo natural depois da V5 e adicionar checkpoint do LangGraph no
PostgreSQL. Isso permite retomar grafos apos falha, auditar estado entre nodes e
preparar fluxos com human-in-the-loop.
