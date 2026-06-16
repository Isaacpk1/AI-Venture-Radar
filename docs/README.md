# Documentacao do NVIDIA Startup AI Radar

Este indice mostra como ler a documentacao do projeto sem se perder.

O projeto usa um monolito modular com workers. Cada modulo evolui com suas
proprias versoes.

---

## Leitura Recomendada

Comece por estes documentos:

| Ordem | Documento | Para que serve |
|---|---|---|
| 1 | `docs/estado_atual_do_projeto.md` | Fotografia do estado real atual |
| 2 | `docs/roadmap_proximos_passos.md` | Roadmap modular do projeto |
| 3 | `docs/arquitetura_global_monolito_modular_workers.md` | Arquitetura geral |
| 4 | `docs/validacao_arquitetural_modulos_workers.md` | Validacao de modulos e workers |
| 5 | `docs/validacao_mensagens_interacoes_modulos.md` | Como modulos e filas conversam |

---

## Modulos Implementados

| Modulo | Estado | Documentacao |
|---|---|---|
| scraping | Scraping V8 | `docs/scraping/` |
| agents | Agents V5 | `docs/agents/` |

---

## Modulos Planejados

| Modulo | Proxima versao | Roadmap |
|---|---|---|
| ingestion | Ingestion V1 | `docs/ingestion/roadmap_ingestion.md` |
| startups | Startups V1 | `docs/startups/roadmap_startups.md` |
| embeddings | Embeddings V1 | `docs/embeddings/roadmap_embeddings.md` |
| rag | RAG V1 | `docs/rag/roadmap_rag.md` |
| nvidia_knowledge | NVIDIA Knowledge V1 | `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` |
| recommendations | Recommendations V1 | `docs/recommendations/roadmap_recommendations.md` |
| briefing | Briefing V1 | `docs/briefing/roadmap_briefing.md` |

---

## Regra de Versionamento

Cada modulo evolui separadamente:

```txt
Scraping V8
Agents V5
Ingestion V1
Embeddings V1
RAG V1
```

Evite pensar em uma unica versao global do projeto. Isso confundiria modulos que
tem ritmos e responsabilidades diferentes.

---

## Regra de Arquitetura

Para novos modulos:

```txt
domain/         regras puras
application/    casos de uso e contratos
infrastructure/ banco, APIs, filas, LLMs e frameworks
factories/      composicao de dependencias
presentation/   rotas HTTP quando fizer sentido
tests/          unitarios e integracao
```

Workers ficam fora dos modulos e recebem mensagens pequenas:

```txt
workers/<nome_do_worker>
mensagem = somente identificadores
```

O estado real fica em banco, nao na fila.
