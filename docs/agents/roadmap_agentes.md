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
| Agents V8 | Implementado | `docs/agents/agents_v8_extraction_agent.md` |
| Agents V9 | Implementado | `docs/agents/agents_v9_startup_classifier.md` |
| Agents V10 | Implementado | `docs/agents/agents_v10_nvidia_rag_agent.md` |
| Agents V11 | Implementado | `docs/agents/agents_v11_recommendation_agent.md` |
| Agents V12 | Implementado | `docs/agents/agents_v12_briefing_agent.md` |

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
checkpoint PostgreSQL implementado na V6
human-in-the-loop via API implementado na V7
```

### Extraction Agent (Agents V8)

Status:

```txt
implementado
```

Extrai dados estruturados (founders, funding, customers) das evidencias
de uma startup. Desbloqueado pelo Startups V2 (campos de destino).

Entregue:

- `ExtractionGraph` (3 nodes, copia estrutural de
  `StartupClassificationGraph`, sem interrupt nesta versao);
- `LangChainGeminiExtractor` (copia estrutural de
  `LangChainGeminiStartupClassifier`); prompt instrui explicitamente a
  nunca inferir/inventar — devolver vazio/`unknown`/null quando a
  evidencia nao menciona o dado (regra 9 do CLAUDE.md: saida do LLM
  validada via Pydantic, nunca confiada diretamente);
- contrato publico `ExtractionService` (`application/public/extractor.py`);
- `AgentType.EXTRACTION` wired em `ExecuteAgentJob`/`ResumeAgentJob`;
- consumido sincronamente por `startups` via adapter proprio
  (`AgentsExtractor`), mesmo padrao do Startup Classifier — `POST
  /startups/{id}/extract`.

Documento da entrega: `docs/agents/agents_v8_extraction_agent.md`.
Contraparte de dados: `docs/startups/startups_v2_campos_estruturados.md`.

### Startup Classifier Agent (Agents V9)

Status:

```txt
implementado
```

Classifica a maturidade de IA da startup (AI-native/AI-enabled/Non-AI)
com justificativa, a partir do perfil e evidencias. Fechou a lacuna mais
critica do diagnostico (`docs/diagnostico_case_original_e_novas_prioridades.md`,
secao 3).

Entregue:

- `StartupClassificationGraph` (3 nodes, copia estrutural de
  `SearchPlanningGraph`, sem interrupt nesta versao);
- `LangChainGeminiStartupClassifier` (copia estrutural de
  `LangChainGeminiEvidenceJudge`);
- contrato publico `StartupClassifierService`
  (`application/public/startup_classifier.py`);
- `AgentType.STARTUP_CLASSIFIER` wired em `ExecuteAgentJob`/`ResumeAgentJob`;
- consumido sincronamente por `startups` via adapter proprio (nao usa a
  fila `agent_runs` nesta entrega — ver doc da entrega para o porque).

Documento da entrega: `docs/agents/agents_v9_startup_classifier.md`.
Contraparte de dados: `docs/startups/startups_v3_classificacao_maturidade.md`.

### NVIDIA RAG Agent (Agents V10)

Status:

```txt
implementado
```

Consulta a base RAG de conhecimento NVIDIA, com citacoes.

Objetivo:

```txt
pergunta/perfil da startup -> trechos relevantes da base NVIDIA, com
citacoes, para alimentar Recommendation e Briefing Agent
```

Entregue:

- `NvidiaRagGraph` (3 nodes, copia estrutural de `ExtractionGraph`, sem
  interrupt nesta versao) — implementa o contrato publico novo
  `NvidiaRagService` (`application/public/nvidia_rag.py`);
- sem LLM client proprio: o node `query_rag` chama
  `RagQuestionAnswererAdapter`, que implementa a porta interna
  `NvidiaRagToolPort` chamando `rag/application/public/question_answerer.py`
  direto, filtrado por `source_type="nvidia_knowledge"` — a geracao de
  resposta com citacoes ja existe em `rag` V4, este agente so orquestra;
- `AgentType.NVIDIA_RAG` wired em `ExecuteAgentJob`/`ResumeAgentJob`; sem
  consumidor sincrono dedicado ainda, acionavel pela fila generica
  `agent_runs`.

Pre-requisitos:

```txt
RAG V3 (busca hibrida vetorial+lexical) e V4 (reranking) - ENTREGUE
NVIDIA Knowledge V1 com catalogo completo (18 tecnologias) - ENTREGUE
```

Limite conhecido: o agente esta implementado e funcional, mas so retorna
resultado util depois que a NVIDIA Knowledge V2 (ingestao real de
documentacao NVIDIA via scraping/ingestion/embeddings) for executada
contra as fontes do registry — ainda PENDENTE, ver
`docs/nvidia_knowledge/roadmap_nvidia_knowledge.md`. Sem isso, uma
consulta real devolve `RagEvidenceNotFoundError` (sem evidencias indexadas
com `source_type="nvidia_knowledge"`).

Documento da entrega: `docs/agents/agents_v10_nvidia_rag_agent.md`.

### Recommendation Agent (Agents V11)

Status:

```txt
implementado
```

Recomenda tecnologias NVIDIA para uma startup com justificativa revisada.
Nao e' a mesma entrega que `recommendations` V3 (ver
`docs/recommendations/roadmap_recommendations.md` — V3 continua futuro,
sem RAG/`ai_maturity_level`/prioridade no scoring); este agente so
orquestra o que `recommendations` V1 ja entrega.

Entregue:

- `RecommendationAgentGraph` (4 nodes, copia estrutural de `NvidiaRagGraph`
  na entrada/saida do grafo, mas com um node extra de revisao);
- chama `RecommendationGenerator` (`recommendations/application/public/`,
  ja existe desde Orchestration V1) como tool via
  `RecommendationGeneratorAdapter`; nao reescreve `match_technologies()`;
- LLM (`LangChainGeminiRecommendationReviewer`) so julga candidatos com
  `score < 0.5` (banda ambigua) e reescreve a justificativa de todos os
  mantidos em linguagem de negocio — mesmo padrao de escalonamento que
  `scraping` ja usa para chamar `agents` (`AGENT_REVIEW`);
- guarda em codigo: candidato confiante (`score >= 0.5`) nunca e'
  descartado, mesmo se o LLM tentar;
- import circular `agents -> recommendations -> startups -> agents`
  descoberto e corrigido com import lazy.

Documento da entrega: `docs/agents/agents_v11_recommendation_agent.md`.

### Briefing Agent (Agents V12)

Status:

```txt
implementado
```

Gera uma analise final clara para negocio. Nao e' a mesma entrega que
`briefing` V2 (ver `docs/briefing/roadmap_briefing.md` — V2 continua
futuro nesse sentido amplo); este agente so orquestra o que `briefing` V1
ja entrega.

Entregue:

- `BriefingAgentGraph` (4 nodes, copia estrutural de
  `RecommendationAgentGraph`, mas sem decisao de manter/descartar — so
  reescrita de prosa);
- chama `BriefingGenerator` (`briefing/application/public/`, ja existe
  desde Orchestration V1) como tool via `BriefingGeneratorAdapter`; nao
  reescreve `build_briefing_markdown()`;
- LLM (`LangChainGeminiBriefingProseRewriter`) sempre reescreve a prosa
  em linguagem executiva — diferente do Recommendation Agent, nao ha
  condicao de "pular" (reescrever a prosa e' o proposito do agente);
- fallback seguro em codigo: se a reescrita perder alguma URL de
  citacao do Markdown original, devolve o Markdown deterministico
  inalterado;
- import lazy de `BriefingFactory` dentro da factory (mesmo ciclo
  `agents -> briefing -> startups -> agents` do Recommendation Agent).

Documento da entrega: `docs/agents/agents_v12_briefing_agent.md`.

## Regra Principal

Um agente coordena fluxo. Ele nao deve concentrar toda a regra de negocio.

O padrao correto e:

```txt
agent -> contratos publicos -> services/use cases/tools -> resultado estruturado
```

## Estado atual e proximo passo (atualizado)

Com `Startup Classifier Agent (V9)`, `Extraction Agent (V8)`,
`NVIDIA RAG Agent (V10)`, `Recommendation Agent (V11)` e agora
`Briefing Agent (V12)` implementados, o Entregavel 2 do case ("sistema
multiagente") esta **completo: 8/8 agentes do brief implementados como
agentes LangGraph de fato** (ver diagnostico, secao 8). Ordem seguida:

```txt
1. Startup Classifier Agent (V9) - ENTREGUE
2. Extraction Agent (V8) - ENTREGUE
3. NVIDIA RAG Agent (V10) - ENTREGUE (chama rag/application/public/ como
   tool; util de verdade so depois que NVIDIA Knowledge V2 rodar contra
   fontes reais, ver item 4)
4. NVIDIA Knowledge V2 (ingestao real de docs NVIDIA via
   scraping/ingestion/embeddings) - em andamento (2/8 fontes P0 validadas
   ponta a ponta), nao bloqueia mais nenhum agente em si, so a qualidade
   das respostas
5. Recommendation Agent (V11) - ENTREGUE (chama
   recommendations/application/public/ como tool + LLM proprio para
   ambiguidade e linguagem de negocio)
6. Briefing Agent (V12) - ENTREGUE (chama briefing/application/public/
   como tool + LLM proprio sempre ativo para reescrever a prosa
   executiva, com fallback seguro contra perda de citacoes)
```

Trabalho restante fora do Entregavel 2: terminar NVIDIA Knowledge V2
contra o resto do registry, dar consumidores sincronos reais a V10/V11/V12
(hoje so acionaveis pela fila generica `agent_runs`), e o Entregavel 5
(Frontend) e 6 (Diferencial), que continuam fora do escopo de `agents`.
