# Roadmap do Modulo Recommendations

Atualizado em 26/06/2026.

O modulo `recommendations` cruza perfil de startup, evidencias e conhecimento NVIDIA para gerar recomendacoes explicaveis.

---

## Estado Atual

| Versao | Status | Objetivo |
|---|---|---|
| Recommendations V1 | Implementado | Regras deterministicas iniciais |
| Recommendations V2 | Implementado | RAG grounding com citacoes NVIDIA |
| Recommendations V3 | Implementado | Confidence, complexity e stats para dashboard |
| Recommendations V4 | Futuro | Feedback humano, versionamento e revisao |

---

## V1 - Regras Deterministicas

Entregue:

```txt
Recommendation
match deterministico por keywords com word boundary
score inicial
justificativa rastreavel
matched_keywords
evidence_ids
POST /recommendations
GET /recommendations/{id}
GET /recommendations?startup_id=
```

Documento: `docs/recommendations/recommendations_v1_regras_deterministicas.md`.

---

## V2 - RAG Grounding

Entregue em 24/06/2026:

```txt
NvidiaKnowledgeGrounder
RagNvidiaKnowledgeGrounder
consulta a rag/application/public/question_answerer.py
filtro source_type=nvidia_knowledge
citacoes em Markdown clicavel
fallback deterministico quando nao ha contexto ou chave LLM
```

Documento: `docs/recommendations/recommendations_v2_rag_grounding.md`.

---

## V3 - Confidence, Complexity e Stats

Entregue em 25/06/2026:

```txt
recommendations.confidence
recommendations.complexity
GET /recommendations/stats?limit=10
TechnologyStats para dashboard
```

Migration: `d7e3f1a2b9c4_add_confidence_complexity_to_recommendations.py`.

A rota de stats alimenta o dashboard do Frontend V4 com as tecnologias NVIDIA mais recomendadas no portfolio.

---

## V4 - Futuro

Campos e fluxos que ficam para revisao humana:

```txt
aprovar/rejeitar recomendacoes
registrar comentarios
versionar geracoes
separar justificativa tecnica de justificativa de negocio
riscos e tradeoffs estruturados
```

---

## Tecnologias candidatas

| Fraqueza confirmada | Abordagem | Status |
|---|---|---|
| Justificativa template sem citar conteudo NVIDIA | Reusar `rag/application/public/question_answerer.py` filtrado por `source_type=nvidia_knowledge` | Concluido em V2 |
| Dashboard precisava de top tecnologias | Agregacao em backend e `GET /recommendations/stats` | Concluido em V3 |
| Sem versionamento de geracoes | Adicionar historico/versionamento antes de feedback humano | Futuro |
| Setores fora do vocabulario do catalogo podem nao bater keyword | Complementar match com busca semantica via embeddings | Futuro |
