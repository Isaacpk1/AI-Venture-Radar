# Decisoes Pendentes do Projeto

Criado em 23/06/2026. Limpo em 23/06/2026 apos a rodada de decisoes —
todas as 6 secoes originais foram resolvidas e movidas pra documentacao
"viva" (ver tabela abaixo). Sobrou so 1 pergunta em aberto.

---

## 1. Qual diferencial apresentar no case (P3)?

```txt
Candidatos ja listados no roadmap (docs/roadmap_produto_final.md, P3):
rastreabilidade ponta a ponta (toda recomendacao e citacao tem origem
rastreavel), hibrido deterministico + agente por excecao (regra de codigo
decide quando vale chamar LLM), ou cobertura do NVIDIA Inception (catalogo
+ 17/20 fontes reais ingeridas).
```

Essa escolha muda o que vale priorizar no frontend e na demo — ex: se o
diferencial e' "rastreabilidade", a evidencia clicavel por recomendacao
(ja no roadmap do frontend V3) vira o ponto central da apresentacao, nao
so mais uma feature. Ainda sem resposta.

---

## Decisoes ja resolvidas (histórico — onde foram movidas)

| Pergunta original | Decisao | Onde ficou registrada |
|---|---|---|
| Projeto e' demo ou produto real? | Demo, sem auth real | `docs/roadmap_produto_final.md` (Diagnostico resumido + P2) |
| RAG real em recommendations/briefing? | Sim, decidido | `docs/recommendations/roadmap_recommendations.md` V2, `docs/briefing/roadmap_briefing.md` (extensao V1) |
| BM25/pg_search vale a troca? | Sim ("nao gostei do 0.67") | `docs/rag/roadmap_rag.md`, `docs/roadmap_evolucao_tecnica_mvp.md` Fase 3 |
| Filtro por `startup_id` no RAG? | Nao necessario pro RAG-grounding decidido acima (so seria pro chat por startup, nao pedido ainda) | `docs/rag/roadmap_rag.md` |
| Proteger modelo/dimensao no Qdrant? | Sim, decidido | `docs/embeddings/roadmap_embeddings.md` |
| Sincronia Qdrant<->Postgres? | Sim, decidido | `docs/embeddings/roadmap_embeddings.md` |
| Backup do Qdrant? | Nao agora (demo) | `docs/roadmap_produto_final.md` P2 (fora de escopo) |
| Descoberta de startups — fonte? | 14 hubs gratuitos (StartSe, Distrito, etc.) + 4 fontes de enriquecimento, teto de custo zero/demo | `docs/scraping/roadmap_scraping.md`, secao "Descoberta de startups" |
| Auth completa vs revisao simples? | Revisao simples, sem login | `docs/frontend/roadmap_frontend.md` V5 |
| rapidfuzz pro dedup de startups? | Sim, falta calibrar limiar | `docs/startups/roadmap_startups.md` |
| recharts vs SVG pros graficos? | Recharts | `docs/frontend/roadmap_frontend.md`, `docs/mapa_tecnologias.md` |
| NVIDIA RAG Agent (V10) sem uso — redesenhar? | Nao, deixar como esta — RAG-grounding em recommendations/briefing cobre o mesmo proposito por outro caminho | `docs/agents/roadmap_agentes.md` |

Sequencia de implementacao de tudo isso: ver "Ordem de implementacao
recomendada" em `docs/roadmap_produto_final.md`.

---

## Como usar este documento

Mesma regra de antes: quando a pergunta da secao 1 for respondida, mover
pra `docs/roadmap_produto_final.md` (P3) e apagar a secao 1 tambem — o
documento fica vazio (exceto o historico) quando isso acontecer, o que e'
o estado desejado, nao um problema.
