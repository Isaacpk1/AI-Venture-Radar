# Proximos Passos Para Fechar o MVP

Este documento organiza o que falta para transformar o projeto em uma primeira
versao utilizavel de ponta a ponta.

---

## 1. O Que Ja Existe

```txt
Scraping V8
Agents V7
Ingestion V1
Embeddings V5
Startups V1
RAG V2
NVIDIA Knowledge V1
```

O sistema ja consegue:

```txt
coletar URL publica
validar qualidade da evidencia
persistir scraping_results
limpar e chunkar texto
gerar embeddings em lote
salvar vetores no Qdrant
cadastrar startup
associar evidencias a startup
executar agentes com checkpoint e human-in-the-loop
buscar evidencias semanticamente com POST /rag/search
responder perguntas com citacoes via POST /rag/answer
consultar catalogo NVIDIA via GET /nvidia-knowledge/technologies
```

Validacao unitaria recente:

```txt
297 passed
```

---

## 2. Lacuna Principal

O projeto ainda nao tem uma camada que transforme a base preparada em resposta
ou decisao.

Hoje existem pecas de pipeline:

```txt
POST /scraping/jobs
POST /ingestion/jobs
POST /embeddings/jobs
POST /startups
POST /startups/{id}/evidences
```

Mas ainda nao existe:

```txt
POST /rag/search
POST /rag/answer
POST /recommendations
POST /briefings
POST /analysis/jobs
```

---

## 3. Proxima Entrega: Recommendations V1

Objetivo:

```txt
startup + evidencias + catalogo NVIDIA -> recomendacoes rastreaveis
```

Entregaveis recomendados:

```txt
entidade Recommendation
regras deterministicas por setor/caso de uso
consulta ao catalogo NVIDIA
score inicial de aderencia
justificativa simples e rastreavel
testes unitarios das regras
```

Criterio de pronto:

```txt
uma startup com perfil estruturado recebe recomendacoes iniciais com tecnologia,
score e justificativa
```

---

## 4. Depois do RAG V2

### RAG V2 - Resposta com Citacoes

```txt
implementado
POST /rag/answer
resposta estruturada com citacoes por chunk/source_url
```

### NVIDIA Knowledge V1

```txt
implementado
catalogo inicial de tecnologias NVIDIA
casos de uso
fontes oficiais
metadados basicos
```

### Recommendations V1

```txt
Recommendation
regras deterministicas por setor/caso de uso
score simples
justificativa rastreavel
```

### Briefing V1

```txt
template Markdown
resumo da startup
evidencias principais
recomendacoes
riscos
proximas acoes
```

### Orchestration V1

```txt
analysis_jobs
endpoint unico para rodar pipeline
estado agregado do fluxo
ligacao entre scraping, ingestion, embeddings, startups, rag e briefing
```

---

## 5. Ordem Recomendada

```txt
1. Recommendations V1 - regras deterministicas
2. Briefing V1 - Markdown executivo
3. Orchestration V1 - pipeline end-to-end
4. NVIDIA Knowledge V2 - ingestao de fontes oficiais
5. Hardening de integracao/observabilidade
```

Motivo: cada passo usa o anterior. Recommendations e briefing precisam de RAG
e conhecimento NVIDIA para terem justificativa real.

---

## 6. Riscos Tecnicos

```txt
integracoes dependem de Postgres/Redis/Qdrant locais
GEMINI_API_KEY precisa estar configurada para provider real
sem autenticacao nas rotas
sem frontend
sem endpoint unico de orquestracao
sem limpeza automatica de checkpoints antigos
sem custo real de tokens/LLM
```

---

## 7. Definicao de MVP

MVP minimo:

```txt
entrada: URL ou startup
saida: briefing Markdown com fontes e recomendacoes NVIDIA iniciais
```

Fluxo necessario:

```txt
scraping -> ingestion -> embeddings -> RAG -> recommendations -> briefing
```

O projeto ja tem scraping, ingestion, embeddings, startups basico e busca
semantica com resposta citada, alem de catalogo NVIDIA inicial. A proxima etapa
e recommendations.
