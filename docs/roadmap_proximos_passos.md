# Roadmap Modular do Projeto

Este documento mostra a evolucao do NVIDIA Startup AI Radar a partir do estado
atual do sistema.

A regra principal agora e:

```txt
cada modulo tem suas proprias versoes
o projeto nao deve virar uma sequencia unica de V1, V2, V3 gigante
```

Scraping pode estar na V8 enquanto agents esta na V7, ingestion na V1 e RAG
na V2. Isso e normal e deixa a arquitetura mais facil de entender.

---

## 1. Estado Atual

| Modulo | Estado | Versao atual |
|---|---|---|
| scraping | maduro para a primeira fase | Scraping V8 |
| agents | base multiagente funcional | Agents V7 |
| ingestion | implementado | Ingestion V1 + worker |
| embeddings | implementado | Embeddings V5 |
| startups | implementado | Startups V1 |
| rag | implementado | RAG V2 |
| nvidia_knowledge | ainda nao implementado | futuro NVIDIA Knowledge V1 |
| recommendations | ainda nao implementado | futuro Recommendations V1 |
| briefing | ainda nao implementado | futuro Briefing V1 |

---

## 2. Ordem Macro Recomendada

A ordem macro de construcao planejada era:

```txt
1. consolidar agents quando necessario
2. criar ingestion
3. criar startups
4. criar embeddings + Qdrant
5. criar RAG
6. criar NVIDIA Knowledge
7. criar recommendations
8. criar briefing
9. evoluir dashboard/API de consulta
10. fortalecer observabilidade e producao
```

Essa ordem existe porque cada camada alimenta a proxima:

```txt
scraping -> scraping_results
ingestion -> documents/chunks
embeddings -> vetores no Qdrant
rag -> respostas com evidencias
recommendations -> match startup/tecnologia NVIDIA
briefing -> relatorio executivo
```

Estado atual dessa ordem:

```txt
1. scraping/agents       -> implementado
2. ingestion             -> implementado
3. startups              -> implementado em V1 basico
4. embeddings + Qdrant   -> implementado ate V5 operacional
5. RAG                   -> V2 implementado
6. NVIDIA Knowledge      -> proximo bloco
```

---

## 3. Proximos Passos Imediatos

Com ingestion, embeddings e startups basicos ja implementados, existem dois
caminhos bons agora.

### Caminho tecnico

```txt
Hardening de producao
```

Esse caminho melhora a robustez operacional:

- rodar testes de integracao com Postgres/Redis/Qdrant;
- aplicar migrations em ambiente local limpo;
- validar workers reais com Redis;
- adicionar observabilidade basica;
- revisar autenticacao/autorizacao das rotas.

### Caminho de produto

```txt
NVIDIA Knowledge V1 - catalogo inicial
```

Esse caminho usa o que ja foi construido:

- RAG V2 ja busca evidencias e gera resposta citada;
- startups ja tem modelo relacional basico;
- recommendations precisa de catalogo NVIDIA para gerar justificativa tecnica.

Recomendacao atual:

```txt
fazer NVIDIA Knowledge V1 agora
manter hardening de integracao como trilha tecnica paralela
```

Motivo: o projeto ja consegue responder com evidencias. Agora falta uma base
NVIDIA citavel para alimentar recomendacoes e briefings.

---

## 4. Roadmaps por Modulo

| Modulo | Documento |
|---|---|
| scraping | `docs/scraping/modulo_scraping_atualizado.md` |
| agents | `docs/agents/roadmap_agentes.md` |
| ingestion | `docs/ingestion/roadmap_ingestion.md` |
| startups | `docs/startups/roadmap_startups.md` |
| embeddings | `docs/embeddings/roadmap_embeddings.md` |
| rag | `docs/rag/roadmap_rag.md` |
| nvidia_knowledge | `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` |
| recommendations | `docs/recommendations/roadmap_recommendations.md` |
| briefing | `docs/briefing/roadmap_briefing.md` |

---

## 5. Regra Arquitetural para Novos Modulos

Todo modulo novo deve seguir a mesma estrutura base:

```txt
domain/         entidades, enums, regras puras
application/    casos de uso, DTOs, ports, contratos publicos
infrastructure/ banco, APIs externas, LLM, filas, frameworks
factories/      composicao das dependencias concretas
presentation/   rotas HTTP quando fizer sentido
tests/          unitarios e integracao
```

Workers ficam fora dos modulos:

```txt
workers/<nome_do_worker>/
```

E devem receber apenas identificadores:

```txt
job_id
run_id
document_id
chunk_id
recommendation_id
```

O estado real fica em PostgreSQL, Qdrant ou outro armazenamento apropriado. A
fila nao deve virar banco de dados.

---

## 6. Como Ler as Versoes

Exemplo correto:

```txt
Scraping V8
Agents V7
Ingestion V1
Embeddings V5
Startups V1
RAG V2
```

Isso quer dizer que cada modulo evolui no seu proprio ritmo.

Nao usamos:

```txt
Projeto V9
Projeto V10
Projeto V11
```

Esse modelo ficaria confuso porque misturaria responsabilidades diferentes.

---

## 7. Criterio de Pronto do Projeto

O projeto chega em uma primeira versao completa quando conseguir executar este
fluxo:

```txt
1. coletar evidencia publica de uma startup
2. validar se a evidencia e util
3. persistir conteudo aprovado
4. transformar conteudo em documents/chunks
5. gerar embeddings
6. buscar evidencias semanticamente
7. consolidar perfil da startup
8. responder perguntas com citacoes
9. consultar conhecimento NVIDIA
10. recomendar tecnologias NVIDIA
11. gerar briefing executivo com fontes
```

Hoje ja temos os passos 1, 2, 3, 4, 5, 6, 8 e parte do 7 em boa forma. O
proximo bloco e criar a base NVIDIA Knowledge.
