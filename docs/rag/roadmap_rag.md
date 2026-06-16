# Roadmap do Modulo RAG

O modulo `rag` responde perguntas usando evidencias recuperadas. Ele deve
buscar antes de gerar.

RAG significa Retrieval-Augmented Generation:

```txt
pergunta -> busca evidencias -> monta contexto -> LLM responde com fontes
```

---

## Objetivo do Modulo

```txt
responder perguntas sobre startups com base em evidencias citaveis
```

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| RAG V1 | Futuro | Busca semantica simples |
| RAG V2 | Futuro | Resposta com citacoes |
| RAG V3 | Futuro | Busca hibrida |
| RAG V4 | Futuro | Reranking |
| RAG V5 | Futuro | Avaliacao de qualidade |

---

## RAG V1 - Busca Semantica Simples

Entregaveis:

- modulo `apps/api/src/modules/rag`;
- contrato publico `Retriever`;
- busca por similaridade no Qdrant;
- retorno de chunks com score e fonte;
- testes com repositorio fake.

Criterio de pronto:

```txt
uma pergunta retorna chunks relevantes com referencia ao document/chunk original
```

---

## RAG V2 - Resposta com Citacoes

Entregaveis:

- montagem de contexto;
- prompt de resposta fundamentada;
- saida estruturada com resposta e citacoes;
- validacao para impedir resposta sem fonte.

---

## RAG V3 - Busca Hibrida

Entregaveis:

- combinar busca vetorial com filtros estruturados;
- filtrar por startup, fonte, data e tipo de evidencia;
- usar PostgreSQL junto com Qdrant.

---

## RAG V4 - Reranking

Entregaveis:

- reranker para ordenar evidencias;
- remocao de chunks redundantes;
- limite de tokens por contexto;
- explicacao de por que cada fonte entrou.

---

## RAG V5 - Avaliacao

Entregaveis:

- dataset fixo de perguntas;
- avaliacao de citacoes;
- avaliacao de resposta sem alucinacao;
- regressao de prompt.
