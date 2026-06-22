# Arquitetura Global - Monolito Modular + Workers

Atualizado em 22/06/2026.

---

## Visao Geral

```txt
FastAPI
  -> modulos sincronicos
  -> jobs em PostgreSQL
  -> workers Dramatiq para tarefas longas
  -> Qdrant para busca vetorial
  -> LangGraph para agentes
```

O backend e um monolito modular. Cada modulo tem suas fronteiras e evolui em
versoes proprias.

---

## Modulos

```txt
scraping           coleta e valida evidencias publicas
agents             grafos LangGraph e agent_runs
ingestion          documents/chunks a partir de scraping_results
embeddings         embeddings e Qdrant
startups           perfil relacional, evidencias, extracao e classificacao
rag                busca hibrida, reranking e resposta citada
nvidia_knowledge   catalogo NVIDIA e futura base de docs oficiais
recommendations    recomendacoes NVIDIA rastreaveis
briefing           briefing executivo em Markdown
orchestration      analysis_jobs e encadeamento recommendations->briefing
```

---

## Workers

```txt
workers/scraper_worker      fila scraping   job_id
workers/agent_worker        fila agents     run_id
workers/ingestion_worker    fila ingestion  job_id
workers/embedding_worker    fila embeddings job_id
```

Workers nao contem regra de negocio; apenas recebem IDs e chamam factories/use
cases.

---

## Fluxos

### Coleta e Preparacao

```txt
POST /scraping/jobs
-> scraper_worker
-> scraping_results
-> POST /ingestion/jobs
-> ingestion_worker
-> documents/chunks
-> POST /embeddings/jobs
-> embedding_worker
-> Qdrant
```

### Perfil e Classificacao

```txt
POST /startups
POST /startups/{id}/evidences
POST /startups/{id}/extract
POST /startups/{id}/classify
```

### RAG e Recomendacao

```txt
POST /rag/search
POST /rag/answer
GET  /nvidia-knowledge/technologies
POST /recommendations
POST /briefings
POST /analysis/jobs
```

---

## Estado Atual

O MVP backend por startup existente esta funcional:

```txt
startup_id -> recommendations -> briefing -> analysis_job
```

O fluxo por URL bruta ainda precisa de Orchestration V2:

```txt
URL -> scraping -> ingestion -> embeddings -> startup/extract/classify
-> recommendations -> briefing
```

---

## Proximas Decisoes Arquiteturais

```txt
1. Como separar conteudo NVIDIA de evidencias de startups no RAG
2. Como persistir/identificar documentos oficiais NVIDIA em Knowledge V2
3. Como Agents V10-V12 chamarao modulos existentes como tools
4. Como expor o fluxo completo para frontend
```
