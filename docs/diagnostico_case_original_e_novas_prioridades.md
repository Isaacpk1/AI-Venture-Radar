# Diagnostico: Aderencia ao Case Original e Novas Prioridades

Este documento compara o brief original do case "NVIDIA Startup AI Radar"
com o que foi efetivamente implementado at hoje, e propoe a ordem de
prioridades daqui para frente. Ele nao substitui
`docs/roadmap_proximos_passos.md` nem `docs/estado_atual_do_projeto.md` —
complementa os dois com a perspectiva do brief original, que ainda nao
tinha sido cruzado formalmente contra o codigo.

---

## 1. Por que este documento existe

Ate esta entrega, o roadmap interno (`docs/roadmap_proximos_passos.md`,
`docs/proximos_passos_mvp.md`) guiou a sequencia de construcao:
scraping -> ingestion -> embeddings -> startups -> RAG -> recommendations
-> briefing -> orchestration. Essa sequencia e coerente e foi seguida sem
pular etapas.

O brief original do case, porem, descreve uma arquitetura especifica
(sistema **multiagente** com LangGraph, RAG com **busca hibrida +
reranking**, startups com **founders/funding/clientes** estruturados, base
de conhecimento cobrindo o **programa NVIDIA Inception** em si, nao so
produtos tecnicos). Cruzando os dois, aparecem lacunas que nao estavam
visiveis so olhando o roadmap interno.

---

## 2. Aderencia por entregavel oficial

| # | Entregavel do case | Estado | Observacao |
|---|---|---|---|
| 1 | Pipeline de scraping | Completo | Scraping V8 |
| 2 | Sistema multiagente (LangGraph) | Parcial (5/8 agentes) | Ver secao 3 |
| 3 | RAG NVIDIA com reranking | Completo | RAG V4: busca hibrida (vetorial+lexical, RRF) + Cohere Rerank |
| 4 | Motor de recomendacao | Parcial | Recommendations V1 entrega o cruzamento, mas determinístico por keyword; classificacao da startup ja existe (Agents V9/Startups V3) mas `recommendations` ainda nao a consulta, e nao usa o RAG |
| 5 | Interface web | Nao iniciado | Stack ja decidida em CLAUDE.md (Next.js + TS + Tailwind + TanStack Query), zero codigo |
| 6 | Diferencial do projeto | Nao iniciado | Ver secao 6 |

---

## 3. Sistema multiagente: o que falta e por que nao e "atraso"

O brief pede 8 agentes LangGraph. Hoje existem 5 implementados como
agentes de fato (`agents` module V10) e os outros 2 (Recommendation,
Briefing) ainda sao **modulos deterministicos de codigo**, nao agentes:

| Agente do brief | Estado | Onde vive hoje |
|---|---|---|
| Search Planner Agent | Implementado | `agents` (SearchPlanningGraph) |
| Scraper Agent | Implementado (nao e um "agente" LLM, e o pipeline `scraping`) | `scraping` V8 |
| Extractor Agent | **Implementado** | `agents` V8 (`docs/agents/agents_v8_extraction_agent.md`) |
| Evidence Validator Agent | Implementado | `agents` (EvidenceValidationGraph) |
| Startup Classifier Agent | **Implementado** | `agents` V9 + `startups` V3 (`docs/agents/agents_v9_startup_classifier.md`) |
| NVIDIA RAG Agent | **Implementado** | `agents` V10, chama `rag/application/public/` como tool (`docs/agents/agents_v10_nvidia_rag_agent.md`); util de verdade so depois que NVIDIA Knowledge V2 ingerir docs reais |
| Recommendation Agent | Nao implementado como agente | `recommendations` V1 resolve a logica via regra de codigo; "Agent Recommendation" ja era planejado como `recommendations` V3 e `agents` V11 |
| Briefing Agent | Nao implementado como agente | `briefing` V1 resolve via template determinístico; "Agente de Briefing" ja era planejado como `briefing` V2 e `agents` V12 |

**Ponto importante:** nenhum desses gaps e surpresa. Os roadmaps internos
de `agents`, `recommendations` e `briefing` *ja* previam exatamente essas
versoes futuras antes deste diagnostico — a decisao de construir a base
determinística primeiro e os agentes depois foi deliberada (regra do
CLAUDE.md: "LLM/agente so quando a validacao determinística nao for
suficiente"). O que faltava era a peca que conecta as duas pontas:

- **Startup Classifier e a lacuna mais critica.** Hoje `Recommendation`
  e gerado direto do texto livre de `Startup.sector`/`description`, sem
  nenhuma classificacao AI-native / AI-enabled / Non-AI no meio. O proprio
  `Startup` nao tem esse campo. Classificar a partir de evidencias
  heterogeneas e exatamente o tipo de julgamento ambiguo que o CLAUDE.md
  reserva para LLM/agente (nao e um limiar simples) — bom primeiro
  candidato a agente "de verdade".

### Como reconciliar sem jogar fora o trabalho determinístico

Caminho confirmado e ja aplicado no Startup Classifier Agent: tratar os
modulos deterministicos (`recommendations`, `briefing`) como **tools**
chamados por um agente LangGraph fino, no mesmo padrao que `scraping` ja
usa para escalar a `agents` (`SemanticInvestigator`, acionado so quando a
validacao determinística e insuficiente). Repetir para os agentes que
faltam:

```txt
Recommendation Agent  = grafo LangGraph que chama RecommendationGenerator
                         (recommendations/application/public/) como tool,
                         e so aciona LLM quando o score for ambiguo ou para
                         enriquecer a justificativa de negocio
Briefing Agent         = grafo LangGraph que chama BriefingGenerator
                         (briefing/application/public/) como tool, e usa
                         LLM para a prosa executiva (Briefing V2 ja previa
                         exatamente isso)
```

Isso satisfaz o Entregavel 2 ("sistema multiagente") sem reescrever a
logica ja validada — o LLM entra na camada de orquestracao/raciocinio, os
modulos continuam sendo a fonte determinística de verdade (regra 6 do
CLAUDE.md).

---

## 4. RAG: busca hibrida e reranking — ENTREGUE

Status:

```txt
entregue
```

`rag` V2 so fazia busca vetorial (Qdrant) + resposta com citacoes. O
brief pedia explicitamente busca vetorial + lexical (BM25) e reranking
(Cohere Rerank) — ambos entregues:

```txt
busca lexical (PostgreSQL full-text search, nao BM25 via lib Python)
  + fusao RRF                              -> RAG V3 (entregue)
reranking via Cohere Rerank, degradacao
  graciosa sem API key                     -> RAG V4 (entregue)
```

Ver `docs/rag/rag_v3_busca_hibrida.md` e `docs/rag/rag_v4_reranking.md`.
O `NVIDIA RAG Agent` (Agents V10, item 4 da secao 8, ja ENTREGUE) usa essa
base de recuperacao como tool.

---

## 5. Conteudo da base de conhecimento NVIDIA — ENTREGUE

Status:

```txt
entregue
```

O catalogo estatico (`nvidia_knowledge` V1) tinha 10 tecnologias. O brief
(secao 5.4) lista 16. Os 8 itens faltantes foram adicionados (ver
`docs/nvidia_knowledge/roadmap_nvidia_knowledge.md`, "Extensao do catalogo
V1"):

```txt
NVIDIA Inception    <- era o mais critico: e o PROGRAMA que o projeto
                        existe para alimentar (atrair/qualificar/nutrir
                        startups para o Inception). Categoria nova:
                        STARTUP_PROGRAM.
NeMo Guardrails
cuDF
cuML
NVIDIA Omniverse
NVIDIA Isaac
NVIDIA Clara
NVIDIA Morpheus
```

Catalogo agora cobre os 16 itens do brief (mais 2 extras ja existentes:
TensorRT generico e MONAI). 3 categorias novas em
`NvidiaTechnologyCategory`: `STARTUP_PROGRAM`, `ROBOTICS_SIMULATION`,
`CYBERSECURITY`.

`recommendations` ainda nao usa `NVIDIA Inception` nem os outros itens
novos em nenhuma regra especial (o motor de regras existente ja considera
qualquer entrada do catalogo igualmente, via `match_technologies()`) — a
mencao ao programa Inception em si (beneficios, credits, comunidade)
agora e *recuperavel* pelo catalogo, mas ainda nao ha um gatilho
deterministico que sugira "mencionar o Inception" numa recomendacao;
isso ficaria mais natural quando o Recommendation Agent (item 4) usar RAG
em vez de so o catalogo estatico.

---

## 6. Startups: campos estruturados — ENTREGUE

Status:

```txt
entregue (slice inicial)
```

O brief (secao 2) pedia coleta de "empresa, produto, setor, **clientes**,
**funding**, **founders** e tecnologias utilizadas". `Startup` agora tem
`founders`, `funding_stage` (enum), `funding_amount_usd` e `customers`
(`docs/startups/startups_v2_campos_estruturados.md`) — esses dados podem
alimentar regras futuras (ex: "startup com funding > X") e aparecer no
briefing executivo. Deduplicacao/consolidacao multi-fonte (a parte
original de "Startups V2 - Consolidacao de Evidencias") ficou fora desta
entrega, registrada como limite conhecido.

Desbloqueou o Extraction Agent (item 4 da secao 8), que agora tem onde
persistir o que extrai.

---

## 7. Entregavel 6 — Diferencial: candidatos

O brief deixa este item aberto de proposito. Candidatos que já emergem do
que foi construido, sem trabalho novo de pesquisa:

```txt
Rastreabilidade total ponta a ponta: toda recomendacao carrega
  matched_keywords + evidence_ids; todo briefing referencia as evidencias
  que geraram cada recomendacao. Poucos sistemas de recomendacao B2B
  expoem esse nivel de auditoria por padrao.

Hibrido deterministico + agente por excecao: a arquitetura ja decide,
  por regra de codigo, quando vale a pena pagar o custo/latencia de um
  LLM (banda de ambiguidade, ja usado em scraping V7/V8) - isso pode ser
  o proprio argumento de diferenciacao tecnica do projeto, nao so um
  detalhe de implementacao.

Cobertura do programa Inception, nao so produtos tecnicos (depende da
  secao 5 ser resolvida) - poucos approaches tratam "atrair para um
  programa de startups" como parte do dominio de RAG.
```

Nenhuma decisao tomada aqui — fica para discussao quando o restante do
pipeline estiver mais maduro.

---

## 8. Prioridades recomendadas (ordem sugerida)

```txt
1. Startup Classifier — ENTREGUE (Agents V9 + Startups V3, ver
   docs/agents/agents_v9_startup_classifier.md). Recommendations ainda
   nao consome o resultado (Startup.ai_maturity_level) — ajuste menor
   pendente, nao bloqueante.

2. Completar catalogo NVIDIA Knowledge — ENTREGUE (8 itens adicionados,
   Inception incluido; ver docs/nvidia_knowledge/roadmap_nvidia_knowledge.md).

3. RAG V3 (busca hibrida) + V4 (reranking) — ENTREGUE (fecha o
   Entregavel 3 por completo; ver docs/rag/rag_v3_busca_hibrida.md e
   docs/rag/rag_v4_reranking.md).

4. Construir os 2 agentes LangGraph que ainda faltam (Recommendation,
   Briefing) como orquestradores sobre os modulos deterministicos
   existentes — fecha o Entregavel 2. Decisao de design confirmada e ja
   aplicada no Startup Classifier, repetida no Extraction Agent e no
   NVIDIA RAG Agent (tool-calling sobre o contrato publico do modulo
   deterministico, sem LLM client proprio quando o modulo chamado ja
   gera a resposta). Ordem combinada com o usuario:

   ```txt
   Extractor (Agents V8)         ENTREGUE (docs/agents/agents_v8_extraction_agent.md)
   NVIDIA RAG Agent (V10)        ENTREGUE (docs/agents/agents_v10_nvidia_rag_agent.md);
                                  chama rag/application/public/ como tool
   NVIDIA Knowledge V2           PROXIMO PASSO (ingestao real de docs
                                  NVIDIA via scraping/ingestion/embeddings,
                                  ver docs/nvidia_knowledge/roadmap_nvidia_knowledge.md)
                                  -- nao bloqueia mais o agente em si, so
                                  a qualidade das respostas dele
   Recommendation Agent (V11)    sem bloqueio adicional
   Briefing Agent (V12)          sem bloqueio adicional
   ```

5. Startups V2 com campos estruturados (founders/funding/clientes) —
   ENTREGUE (slice inicial, ver secao 6 e
   docs/startups/startups_v2_campos_estruturados.md). Desbloqueia o
   Extraction Agent.

6. Frontend (Entregavel 5) — pode rodar em paralelo a qualquer item acima,
   ja consumindo os endpoints existentes.

7. Diferencial (Entregavel 6) — decidir depois que 1-4 estiverem mais
   solidos, escolhendo entre os candidatos da secao 7 ou outro.
```

Hardening de integracao (rodar a suite de testes de integracao com
Postgres/Redis/Qdrant reais) e Auth continuam pendentes, mas sao
transversais — podem entrar em paralelo a qualquer ponto desta lista sem
bloquear nada.

---

## 9. Referencias

| Documento | Caminho |
|---|---|
| Roadmap geral (sequencia ja percorrida) | `docs/roadmap_proximos_passos.md` |
| Roadmap de agents (versoes futuras V8-V12) | `docs/agents/roadmap_agentes.md` |
| Roadmap de recommendations (V2-V5 futuras) | `docs/recommendations/roadmap_recommendations.md` |
| Roadmap de briefing (V2-V5 futuras) | `docs/briefing/roadmap_briefing.md` |
| Roadmap de RAG (V3-V5 futuras) | `docs/rag/roadmap_rag.md` |
| Roadmap de NVIDIA Knowledge (V2-V4 futuras) | `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` |
| Roadmap de startups (V2-V4 futuras) | `docs/startups/roadmap_startups.md` |
