# Roadmap Modular do Projeto

Este documento mostra a evolucao do NVIDIA Startup AI Radar a partir do estado
atual do sistema.

A regra principal agora e:

```txt
cada modulo tem suas proprias versoes
o projeto nao deve virar uma sequencia unica de V1, V2, V3 gigante
```

Scraping pode estar na V8 enquanto agents esta na V5, ingestion na V1 e RAG
ainda nem comecou. Isso e normal e deixa a arquitetura mais facil de entender.

---

## 1. Estado Atual

| Modulo | Estado | Versao atual |
|---|---|---|
| scraping | maduro para a primeira fase | Scraping V8 |
| agents | base multiagente funcional | Agents V5 |
| ingestion | ainda nao implementado | futuro Ingestion V1 |
| startups | ainda nao implementado | futuro Startups V1 |
| embeddings | ainda nao implementado | futuro Embeddings V1 |
| rag | ainda nao implementado | futuro RAG V1 |
| nvidia_knowledge | ainda nao implementado | futuro NVIDIA Knowledge V1 |
| recommendations | ainda nao implementado | futuro Recommendations V1 |
| briefing | ainda nao implementado | futuro Briefing V1 |

---

## 2. Ordem Macro Recomendada

A ordem macro de construcao e:

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

---

## 3. Proximos Passos Imediatos

Existem dois caminhos bons agora.

### Caminho tecnico

```txt
Agents V6 - Checkpoint LangGraph no PostgreSQL
```

Esse caminho melhora a robustez dos agentes:

- retomar grafo apos falha;
- auditar estado entre nodes;
- preparar human-in-the-loop;
- reduzir perda de trabalho em execucoes longas.

### Caminho de produto

```txt
Ingestion V1 - transformar scraping_results em documents/chunks
```

Esse caminho desbloqueia embeddings, Qdrant e RAG:

- limpar conteudo aprovado pelo scraping;
- criar documents rastreaveis;
- criar chunks prontos para embedding;
- preparar o pipeline para busca semantica.

Recomendacao atual:

```txt
fazer Ingestion V1 agora
manter Agents V6 como proxima melhoria de infraestrutura agentica
```

Motivo: o scraping e os agents ja conseguem produzir evidencias. Agora o projeto
precisa transformar essas evidencias em base consultavel.

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
Agents V5
Ingestion V1
Embeddings V1
RAG V1
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
8. consultar conhecimento NVIDIA
9. recomendar tecnologias NVIDIA
10. gerar briefing executivo com fontes
```

Hoje ja temos os passos 1, 2 e 3 em boa forma. O proximo bloco e construir os
passos 4, 5 e 6.
