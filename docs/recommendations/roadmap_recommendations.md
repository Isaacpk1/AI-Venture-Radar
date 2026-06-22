# Roadmap do Modulo Recommendations

O modulo `recommendations` cruza perfil de startup, evidencias e conhecimento
NVIDIA para gerar recomendacoes explicaveis.

---

## Estado Atual

| Versao | Status | Objetivo |
|---|---|---|
| Recommendations V1 | Implementado | Regras deterministicas iniciais |
| Recommendations V2 | Futuro | Recomendacao com RAG |
| Recommendations V3 | Futuro | Agent Recommendation (= Agents V11) |
| Recommendations V4 | Futuro | Ranking, confianca e acao sugerida |
| Recommendations V5 | Futuro | Feedback humano |

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
nao usa Startup.ai_maturity_level no scoring
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
```

---

## Recommendations V3 - Agent Recommendation

Mesma entrega que Agents V11.

Decisao de design:

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

---

## Recommendations V5 - Feedback Humano

```txt
aprovar/rejeitar recomendacoes
registrar comentarios
usar feedback para avaliacao futura
```
