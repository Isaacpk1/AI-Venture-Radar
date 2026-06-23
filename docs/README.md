# Documentacao do NVIDIA Startup AI Radar

Este indice mostra como ler a documentacao atual sem cair em notas historicas
antigas.

Fonte de verdade operacional em 22/06/2026:

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
| startups | Startups V3 | `docs/startups/` |
| rag | RAG V4 | `docs/rag/` |
| nvidia_knowledge | NVIDIA Knowledge V1 expandido + V2 source registry + url_ingestion_jobs | `docs/nvidia_knowledge/` |
| recommendations | Recommendations V1 | `docs/recommendations/` |
| briefing | Briefing V1 | `docs/briefing/` |
| orchestration | Orchestration V1 + V2 parcial | `docs/orchestration/` |

---

## Entregas Do Case Original

| Entregavel | Estado |
|---|---|
| Pipeline de scraping | Completo |
| Sistema multiagente LangGraph | Completo: 8/8 agentes implementados |
| RAG NVIDIA com busca hibrida + reranking | Completo |
| Motor de recomendacao | Parcial: V1 deterministico entregue |
| Interface web | Nao iniciado |
| Diferencial do projeto | Candidatos mapeados, decisao pendente |

---

## Proxima Ordem Recomendada

```txt
1. Fechar Orchestration V2 da URL ate briefing
2. Construir o frontend sobre esse fluxo
3. Completar a base NVIDIA real e enriquecer recommendations
4. Revisao humana e exportacao
5. Hardening: auth, observabilidade, CI/CD e deploy
```

Observacao: o MVP backend macro ja existe. O que falta agora e aderencia total
ao case original, experiencia de usuario e robustez de producao.
