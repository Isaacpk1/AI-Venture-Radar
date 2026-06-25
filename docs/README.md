# Documentacao do NVIDIA Startup AI Radar

Este indice mostra como ler a documentacao atual sem cair em notas historicas
antigas.

Fonte de verdade operacional em 24/06/2026:

```txt
docs/diagnostico_case_original_e_novas_prioridades.md
docs/estado_atual_do_projeto.md
CLAUDE.md
docs/roadmap_produto_final.md
```

---

## Leitura Recomendada

| Ordem | Documento | Uso |
|---|---|---|
| 1 | `docs/diagnostico_case_original_e_novas_prioridades.md` | Aderencia ao brief original e prioridades reais |
| 2 | `docs/estado_atual_do_projeto.md` | Fotografia operacional atual |
| 3 | `docs/roadmap_proximos_passos.md` | Roadmap macro atualizado |
| 4 | `docs/validacao_arquitetural_modulos_workers.md` | Validacao de modulos, workers e contratos |
| 5 | `docs/validacao_mensagens_interacoes_modulos.md` | Como os modulos conversam |
| 6 | `docs/roadmap_produto_final.md` | Backlog priorizado para fechar o produto |
| 7 | `docs/frontend/nextjs_arquitetura.md` | Arquitetura e plano de inicio do frontend Next.js |
| 8 | `docs/frontend/roadmap_frontend.md` | Versoes e entregas planejadas do frontend |

---

## Modulos Atuais

| Modulo | Estado | Docs |
|---|---|---|
| scraping | Scraping V8 | `docs/scraping/` |
| agents | Agents V12 | `docs/agents/` |
| ingestion | Ingestion V1 + worker | `docs/ingestion/` |
| embeddings | Embeddings V5 + worker | `docs/embeddings/` |
| startups | Startups V4 (slice inicial): listagem paginada + dedup por nome/dominio (`rapidfuzz`) | `docs/startups/` |
| rag | RAG V4 | `docs/rag/` |
| nvidia_knowledge | NVIDIA Knowledge V1 expandido + V2 completo (20/20 fontes, 17/20 com conteudo) | `docs/nvidia_knowledge/` |
| recommendations | Recommendations V2 (RAG grounding) | `docs/recommendations/` |
| briefing | Briefing V3 (RAG grounding + export PDF) | `docs/briefing/` |
| orchestration | Orchestration V1 + V2 completa | `docs/orchestration/` |

---

## Entregas Do Case Original

| Entregavel | Estado |
|---|---|
| Pipeline de scraping | Completo |
| Sistema multiagente LangGraph | Completo: 8/8 agentes implementados, 2 (Recommendation/Briefing) ja com consumidor sincrono real em orchestration |
| RAG NVIDIA com busca hibrida + reranking | Completo |
| Motor de recomendacao | V2: regras deterministicas + justificativa fundamentada via RAG (NVIDIA Knowledge), com fallback deterministico |
| Interface web | V1+V2+V3 entregues (portfolio, historico global de jobs, badge de fit, evidencia clicavel, chatbot NVIDIA Knowledge, export PDF); so revisao humana/auth (V5) pendente |
| Diferencial do projeto | **Decidido (24/06/2026): rastreabilidade ponta a ponta** — implementado (citacoes NVIDIA como link Markdown real + frontend renderiza Markdown de verdade) |

---

## Proxima Ordem Recomendada

(Atualizado 25/06/2026 — Startups V4 (dedup por nome/dominio com
`rapidfuzz`, limiar 92 calibrado com 17 pares reais), limpeza de vetores
orfaos no Qdrant (`delete_by_document_id` + `_cleanup_superseded_vectors`),
Frontend V3 e P3 completos. `docs/decisoes_pendentes.md` nao tem pergunta
em aberto.)

```txt
1. Descoberta de startups por fontes gratuitas (StartSe, Distrito,
   Endeavor etc.)
2. Frontend V4 (graficos, comparacao, fila em lote)
```

Observacao: hardening de producao (auth, CI/CD, deploy, backup do Qdrant)
foi decidido como fora de escopo deliberadamente — este projeto continua
case/demo, nao um alvo de producao (ver `docs/decisoes_pendentes.md`,
tabela "Decisoes ja resolvidas"). O que falta agora e' aderencia total ao
case original e experiencia de usuario, nao robustez de producao.
