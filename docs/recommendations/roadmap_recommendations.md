# Roadmap do Modulo Recommendations

O modulo `recommendations` cruza perfil de startup, evidencias e conhecimento
NVIDIA para gerar recomendacoes explicaveis.

---

## Estado Atual

| Versao | Status | Objetivo |
|---|---|---|
| Recommendations V1 | Implementado | Regras deterministicas iniciais |
| Recommendations V2 | Implementado (24/06/2026) | Recomendacao com RAG |
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

**Decidido em 23/06/2026** (`docs/decisoes_pendentes.md`, secao 2): vale
fazer, junto com a mesma decisao para `briefing`.

**Implementado em 24/06/2026:** `NvidiaKnowledgeGrounder`
(`application/ports.py`) + adapter `RagNvidiaKnowledgeGrounder`
(`infrastructure/rag_adapters/`) chamam
`rag/application/public/question_answerer.py` filtrado por
`source_type="nvidia_knowledge"`, 1 chamada em paralelo por tecnologia
candidata (`asyncio.gather`), e substituem a justificativa-template por
texto fundamentado com citacoes reais quando ha contexto recuperavel.
Best-effort: sem `GEMINI_API_KEY` ou sem citacao real, cai pro template
deterministico de V1 (sem erro). Ver
`docs/recommendations/recommendations_v2_rag_grounding.md` para o
detalhamento completo, incluindo limites conhecidos desta entrega
(nao usa evidencia especifica da startup como query, sem cache de
chamada RAG).

**Bug real corrigido em 24/06/2026** (fechamento do P3 — diferencial
"rastreabilidade ponta a ponta", `docs/decisoes_pendentes.md`):
`citation_urls` viravam texto puro (`Fontes: url1, url2`) em
`_build_grounded_justification()`, nao link Markdown — ficavam
ilegiveis como link quando o frontend passou a renderizar
`justification` como Markdown de verdade. Corrigido pra
`[Fonte N](url)` por citacao.

Pre-requisitos ja entregues:

```txt
RAG V3 - busca hibrida
RAG V4 - reranking
```

Pre-requisito que era pendente, ja desbloqueado em 23/06/2026:

```txt
NVIDIA Knowledge V2 - 20/20 fontes processadas, 17/20 com conteudo
recuperavel via /rag/search (ver CLAUDE.md, secao "Recent validation", e
docs/nvidia_knowledge/roadmap_nvidia_knowledge.md). Os 3 gaps restantes
(nvidia-nim-docs, monai-docs, rapids-docs) nao bloqueiam o restante do
catalogo.
```

Entregaveis:

```txt
consultar conhecimento NVIDIA via RAG               - entregue
montar contexto                                     - entregue (delegado ao RagQuestionAnswerer)
gerar recomendacao com citacoes                     - entregue
usar RAG NVIDIA com citacoes para enriquecer a justificativa  - entregue
consultar evidencias especificas da startup como query do RAG - NAO entregue,
  ver limite conhecido em recommendations_v2_rag_grounding.md secao 5
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

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

Confirmado em `domain/policies.py`: `match_technologies()` so faz keyword
matching com word boundary (fix de 23/06/2026); a justificativa gerada e'
um template fixo ("keywords matched. Use case: X."), nunca fundamentada em
conteudo real.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| Justificativa e' template fixo, sem citar conteudo NVIDIA real | chamar `rag/application/public/question_answerer.py` (contrato ja existe, usado pelo NVIDIA RAG Agent V10) filtrado por `source_type="nvidia_knowledge"` para fundamentar a justificativa de cada recomendacao com citacoes reais — **CONCLUIDO em 24/06/2026** (ver `recommendations_v2_rag_grounding.md`) | Recommendations V2 (Recomendacao com RAG) | Medio — integracao de contrato publico ja existente, zero tech nova |
| `match_technologies()` so encontra startups cujo texto bate keyword; setor fora do catalogo (ex: termos em portugues sem alias) nunca aparece | usar o `VectorRepository` (`embeddings/application/public/`, ja existe) para buscar tecnologias por similaridade semantica quando o keyword match nao encontrar nada, como complemento (nao substituto) da regra deterministica | Recommendations V2/V4 | Medio — reuso de contrato publico, sem infra nova |
| Sem versionamento — `generate()` deleta e recria a cada chamada | guardar `generated_at`/numero de geracao por chamada (modelagem de dados, sem lib nova) | Pre-requisito leve para V5 (Feedback humano) — precisa saber a qual geracao um feedback se refere | Baixo |

Nao trocar `match_technologies()` por um motor de ML/classificador
treinado: o volume de dados (poucas dezenas de tecnologias no catalogo) nao
justifica treinamento; busca semantica via embeddings ja existentes resolve
o caso real sem nova infraestrutura.
