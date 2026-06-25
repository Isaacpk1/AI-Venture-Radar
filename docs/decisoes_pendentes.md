# Decisoes Pendentes do Projeto

Criado em 23/06/2026. Limpo em 23/06/2026 apos a rodada de decisoes —
todas as 6 secoes originais foram resolvidas e movidas pra documentacao
"viva" (ver tabela abaixo). A unica pergunta que tinha sobrado (P3, secao
1) foi respondida em 24/06/2026 — ver tabela. Documento sem pergunta em
aberto agora (estado desejado, nao um problema).

**Nota sobre referencias antigas (adicionada 24/06/2026):** antes da
limpeza, este arquivo tinha 6 secoes numeradas. Varios outros docs do
repositorio (`CLAUDE.md`, `docs/roadmap_produto_final.md`,
`docs/roadmap_evolucao_tecnica_mvp.md`, `docs/rag/roadmap_rag.md`,
`docs/embeddings/roadmap_embeddings.md`,
`docs/recommendations/roadmap_recommendations.md`,
`docs/recommendations/recommendations_v2_rag_grounding.md`,
`docs/startups/roadmap_startups.md`, `docs/scraping/roadmap_scraping.md`,
`docs/frontend/roadmap_frontend.md`, `docs/agents/roadmap_agentes.md`,
`docs/briefing/roadmap_briefing.md`, `docs/lacunas_do_projeto.md`) ainda
citam essa numeracao antiga (ex: "secao 2", "secao 5") ao justificar uma
decisao. Esses numeros nao resolvem mais neste arquivo — a numeracao
original nao foi preservada na limpeza. Para achar a decisao citada, use
a tabela "Decisoes ja resolvidas" abaixo e busque pelo assunto/citacao no
texto da doc que referenciou, nao pelo numero da secao.

---

## Decisoes ja resolvidas (histórico — onde foram movidas)

| Pergunta original | Decisao | Onde ficou registrada |
|---|---|---|
| Qual diferencial apresentar no case (P3)? | **Rastreabilidade ponta a ponta** (toda recomendacao e citacao tem origem rastreavel) — decidido 24/06/2026, depois do fechamento do Frontend V3 (badge de fit + evidencia clicavel ja entregues). Os outros 2 candidatos (hibrido deterministico/agente por excecao, cobertura do NVIDIA Inception) ficam como apoio na narrativa, nao como o eixo principal | `docs/roadmap_produto_final.md` (P3) |
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

Quando uma nova pergunta pendente surgir, adicionar uma secao numerada
nova aqui. Quando for respondida, mover a decisao pra tabela "Decisoes
ja resolvidas" acima e apagar a secao — documento sem secao numerada
nenhuma e' o estado desejado, nao um problema.
