# Roadmap do Modulo Recommendations

O modulo `recommendations` cruza perfil de startup, evidencias e conhecimento
NVIDIA para gerar recomendacoes explicaveis.

---

## Estado Atual

| Versao | Status | Objetivo |
|---|---|---|
| Recommendations V1 | Implementado | Regras deterministicas iniciais |
| Recommendations V2 | Futuro | Recomendacao com RAG |
| Recommendations V3 | Futuro (agente entregue em Agents V11) | Agent Recommendation |
| Recommendations V4 | Futuro | Ranking, confianca e acao sugerida |
| Recommendations V5 | Futuro | Feedback humano |

As prioridades transversais de produto estao consolidadas em
`docs/roadmap_produto_final.md`.

---

## Recommendations V1 - Implementado

Entregue:

```txt
Recommendation
match deterministico por keywords
score inicial
justificativa rastreavel
matched_keywords
evidence_ids
POST /recommendations
GET /recommendations/{id}
GET /recommendations?startup_id=
```

Documento: `docs/recommendations/recommendations_v1_regras_deterministicas.md`.

Limite atual:

```txt
nao usa RAG NVIDIA
 usa `Startup.ai_maturity_level` como bonus controlado para candidatos com
 sinal deterministico (entregue em 23/06/2026)
nao gera prioridade/complexidade/proxima acao
```

---

## Recommendations V2 - Recomendacao com RAG

Pre-requisitos ja entregues:

```txt
RAG V3 - busca hibrida
RAG V4 - reranking
```

Pre-requisito ainda pendente:

```txt
NVIDIA Knowledge V2 - documentacao NVIDIA real ingerida e recuperavel
```

Entregaveis:

```txt
consultar evidencias da startup
consultar conhecimento NVIDIA via RAG
montar contexto
gerar recomendacao com citacoes
usar RAG NVIDIA com citacoes para enriquecer a justificativa
```

---

## Recommendations V3 - Agent Recommendation

Status:

```txt
agente entregue (Agents V11, ver docs/agents/agents_v11_recommendation_agent.md)
modulo recommendations em si continua V1 — nao ganhou RAG, ai_maturity_level
  no scoring, nem prioridade/complexidade/proxima acao (isso e' Recommendations
  V2/V4, ainda futuro)
```

O Recommendation Agent (V11) so orquestra o que `recommendations` V1 ja
entrega — nao e' a "mesma entrega" que V2/V4, que mudariam o motor de
regras em si.

Decisao de design (ja aplicada):

```txt
LangGraph orquestra RecommendationGenerator como tool
LLM entra para ambiguidade ou enriquecimento de negocio
match_technologies continua sendo regra deterministica reutilizada
```

---

## Recommendations V4 - Ranking e Confianca

Campos que aproximam o output do brief original:

```txt
nivel de confianca
nivel de prioridade para NVIDIA
complexidade de implementacao
proxima acao sugerida
justificativa de negocio
riscos e tradeoffs
```

Integracao pendente: o Recommendation Agent V11 existe, mas o fluxo
`POST /analysis/jobs` ainda chama apenas o gerador deterministico V1.

---

## Recommendations V5 - Feedback Humano

```txt
aprovar/rejeitar recomendacoes
registrar comentarios
usar feedback para avaliacao futura
```
