# Proximos Passos Para Fechar o Produto

O MVP backend macro ja esta implementado. Este documento agora foca no que falta
para aproximar o projeto do brief original completo.

---

## Ja Existe

```txt
Scraping V8
Agents V12 (8/8 agentes do brief implementados)
Ingestion V1
Embeddings V5
Startups V3
RAG V4
NVIDIA Knowledge V1 expandido
NVIDIA Knowledge V2 source registry + url_ingestion_jobs
Recommendations V1
Briefing V1
Orchestration V1
Orchestration V2 parcial - url_ingestion_jobs + worker automatico (scraping->ingestion->embeddings)
```

Fluxo backend disponivel:

```txt
startup existente -> recommendations -> briefing -> analysis_job
```

Fluxo parcial por URL tambem existe em pecas:

```txt
scraping -> ingestion -> embeddings -> startups/extract/classify
```

Mas ainda falta a orquestracao V2 juntar tudo desde uma URL bruta ate briefing.

---

## Lacunas Reais

### 1. NVIDIA Knowledge V2

```txt
documentacao oficial NVIDIA -> scraping/ingestion -> chunks -> embeddings
-> base RAG filtravel como conteudo NVIDIA
```

Decisao de escopo ja tomada e implementada:

```txt
documents.source_type
Qdrant payload source_type
filtro opcional source_type em /rag/search e /rag/answer
```

Valor default: `startup_evidence`. Conteudo NVIDIA devera usar
`nvidia_knowledge`.

As URLs oficiais NVIDIA ja foram registradas em `/nvidia-knowledge/sources`.
A rota `POST /nvidia-knowledge/ingestion/jobs` ja cria `url_ingestion_jobs`
com `source_type="nvidia_knowledge"`. O advance desses jobs ate embedding
concluido agora e automatico (`workers/orchestration_worker/`, fila
`url_ingestion`) — **rodado e validado contra fontes reais**:
`nemo-framework-docs` e `triton-inference-server-docs` completaram
ponta a ponta e aparecem em `/rag/search` filtrado por `source_type`.
Corrigidos 4 bugs no caminho (3 em `scraping`, 1 em `embeddings`; ver
`docs/nvidia_knowledge/nvidia_knowledge_v2_primeira_validacao_real.md`).
Falta re-testar as outras 6 fontes do lote P0 e rodar P1/P2 — um
problema de resolucao de hostname intermitente do lado Windows (fora do
alcance de uma correcao de codigo) ficou pendente.

### 2. Agentes Do Brief — TODOS ENTREGUES (8/8)

```txt
Agents V10 - NVIDIA RAG Agent - ENTREGUE
Agents V11 - Recommendation Agent - ENTREGUE
Agents V12 - Briefing Agent - ENTREGUE
```

Todos orquestram contratos publicos existentes, sem reimplementar regra de
negocio dentro dos grafos. O NVIDIA RAG Agent (V10) chama
`rag/application/public/question_answerer.py` como tool, sem LLM client
proprio. O Recommendation Agent (V11) vai mais longe: chama
`recommendations/application/public/recommendation_generator.py` como
tool **e** tem LLM proprio, mas so para julgar candidatos ambiguos
(score baixo) e reescrever a justificativa em linguagem de negocio —
nunca recalcula score. O Briefing Agent (V12) chama
`briefing/application/public/briefing_generator.py` como tool e sempre
aciona LLM para reescrever a prosa executiva, com fallback seguro em
codigo se a reescrita perder alguma citacao do Markdown deterministico.

### 3. Recommendation Mais Rica

Recommendations V1 e deterministica (Recommendation Agent V11 orquestra
isso, mas nao muda o motor de regras). Faltam:

```txt
uso de RAG NVIDIA
uso de Startup.ai_maturity_level no scoring
prioridade alto/medio/baixo
complexidade de implementacao
proxima acao para o time NVIDIA
justificativa de negocio separada da tecnica
```

### 4. Frontend

Entregavel oficial ainda nao iniciado.

Telas minimas:

```txt
submeter URL/startup
acompanhar pipeline
ver evidencias e classificacao
ver recomendacoes
ver briefing
revisar/retomar casos com human-in-the-loop
```

### 5. Hardening

```txt
rodar integracao com Postgres/Redis/Qdrant reais
auth/autorizacao
observabilidade
custos e limites de LLM
limpeza de checkpoints
deploy/dev setup reprodutivel
```

---

## Ordem Recomendada

```txt
1. Atualizar/validar docs centrais - feito nesta limpeza
2. NVIDIA Knowledge V2 fundacao source_type - feito
3. NVIDIA Knowledge V2 source registry - feito
4. NVIDIA Knowledge V2 submissao do registry para url_ingestion_jobs - feito
5. Orchestration V2 worker/dispatcher para advance automatico - feito
6. NVIDIA RAG Agent - feito
7. Recommendation Agent - feito (enriquecimento de recommendations em si, V2/V4, continua futuro)
8. Briefing Agent - feito (exportacao/revisao humana/ranking em si, briefing V3/V4/V5, continua futuro)
9. Orchestration V2 por URL bruta
10. Frontend
11. Hardening de producao
```
