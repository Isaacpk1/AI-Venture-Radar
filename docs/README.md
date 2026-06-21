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
| agents | Agents V7 | `docs/agents/` |
| ingestion | Ingestion V1 + worker | `docs/ingestion/` |
| embeddings | Embeddings V5 | `docs/embeddings/` |
| startups | Startups V1 | `docs/startups/` |
| rag | RAG V2 | `docs/rag/` |

---

## Modulos Ainda Pendentes

| Modulo | Proxima versao | Roadmap |
|---|---|---|
| nvidia_knowledge | NVIDIA Knowledge V1 | `docs/nvidia_knowledge/roadmap_nvidia_knowledge.md` |
| recommendations | Recommendations V1 | `docs/recommendations/roadmap_recommendations.md` |
| briefing | Briefing V1 | `docs/briefing/roadmap_briefing.md` |
| orchestration | Pipeline end-to-end | `docs/proximos_passos_mvp.md` |

---

## Regra de Versionamento

Cada modulo evolui separadamente:

```txt
Scraping V8
Agents V7
Ingestion V1
Embeddings V5
Startups V1
RAG V2
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

---

## Proximo Bloco Recomendado

```txt
NVIDIA Knowledge V1
```

Motivo: RAG V2 ja recupera evidencias e gera resposta fundamentada com
citacoes. Falta criar a base de conhecimento NVIDIA para alimentar
recommendations e briefing.
