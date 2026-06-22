# Proximos Passos Para Fechar o Produto

O MVP backend macro ja esta implementado. Este documento agora foca no que falta
para aproximar o projeto do brief original completo.

---

## Ja Existe

```txt
Scraping V8
Agents V9
Ingestion V1
Embeddings V5
Startups V3
RAG V4
NVIDIA Knowledge V1 expandido
Recommendations V1
Briefing V1
Orchestration V1
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

Ainda falta registrar as URLs oficiais NVIDIA e criar o fluxo que ingere essas
fontes com `source_type="nvidia_knowledge"`.

### 2. Agentes Restantes Do Brief

```txt
Agents V10 - NVIDIA RAG Agent
Agents V11 - Recommendation Agent
Agents V12 - Briefing Agent
```

Eles devem orquestrar contratos publicos existentes, nao reimplementar regra de
negocio dentro dos grafos.

### 3. Recommendation Mais Rica

Recommendations V1 e deterministica. Faltam:

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
3. NVIDIA Knowledge V2 registro/ingestao de fontes oficiais
4. NVIDIA RAG Agent
5. Recommendation Agent + enriquecimento de recommendations
6. Briefing Agent
7. Orchestration V2 por URL bruta
8. Frontend
9. Hardening de producao
```
