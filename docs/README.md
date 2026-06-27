# Documentacao do NVIDIA Startup AI Radar

Este indice mostra como ler a documentacao atual sem cair em notas historicas
antigas.

Fonte de verdade operacional em 26/06/2026:

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
| 7 | `docs/frontend/nextjs_arquitetura.md` | Arquitetura do frontend Next.js |
| 8 | `docs/frontend/roadmap_frontend.md` | Versoes e entregas do frontend |
| 9 | `docs/startup_discovery/roadmap_startup_discovery.md` | Descoberta automatica de startups |

---

## Modulos Atuais

| Modulo | Estado | Docs |
|---|---|---|
| scraping | Scraping V8 | `docs/scraping/` |
| agents | Agents V12 | `docs/agents/` |
| ingestion | Ingestion V1 + worker | `docs/ingestion/` |
| embeddings | Embeddings V5 + worker | `docs/embeddings/` |
| startups | Startups V4: campos estruturados, classificacao, paginacao e dedup com `rapidfuzz` | `docs/startups/` |
| rag | RAG V4 | `docs/rag/` |
| nvidia_knowledge | NVIDIA Knowledge V1 expandido + V2 completo (20/20 fontes, 17/20 com conteudo) | `docs/nvidia_knowledge/` |
| recommendations | Recommendations V3: RAG grounding, confidence/complexity e stats | `docs/recommendations/` |
| briefing | Briefing V3: RAG grounding + export PDF | `docs/briefing/` |
| orchestration | Orchestration V1 + V2 completa | `docs/orchestration/` |
| startup_discovery | Startup Discovery V1: 3 hubs publicos + `url_ingestion_jobs` | `docs/startup_discovery/` |
| frontend | Frontend V5: jornada, portfolio, historico, chat, PDF, dashboard, comparacao, lote e revisao humana simples | `docs/frontend/` |

---

## Entregas Do Case Original

| Entregavel | Estado |
|---|---|
| Pipeline de scraping | Completo |
| Sistema multiagente LangGraph | Completo: 8/8 agentes implementados, Recommendation/Briefing com consumidor sincrono em orchestration |
| RAG NVIDIA com busca hibrida + reranking | Completo |
| Motor de recomendacao | V3: regras deterministicas + justificativa via RAG + confidence/complexity + stats |
| Interface web | V1+V2+V3+V4+V5 entregues; auth completa segue fora de escopo |
| Descoberta de startups | V1 entregue para InovAtiva Brasil, Abstartups e 100 Open Startups |
| Diferencial do projeto | Rastreabilidade ponta a ponta implementada: citacoes em Markdown clicavel e evidencia ligada a recomendacao |

---

## Proxima Ordem Recomendada

Atualizado em 26/06/2026. Startups V4, limpeza de vetores orfaos no Qdrant,
Frontend V5, Startup Discovery V1, Recommendations V3 e a primeira fatia da
chain de enriquecimento por dominio estao completos.
`docs/decisoes_pendentes.md` nao tem pergunta em aberto.

```txt
1. Validar a chain de enriquecimento com Tavily real e calibrar ranking/allowlist.
2. Expandir Startup Discovery para mais hubs gratuitos alem dos 3 iniciais.
```

Hardening de producao (auth, CI/CD, deploy, backup do Qdrant) segue fora de
escopo deliberadamente: este projeto continua case/demo, nao alvo de producao.
