# Roadmap do Modulo NVIDIA Knowledge

O modulo `nvidia_knowledge` organiza conhecimento sobre tecnologias NVIDIA para
que o sistema consiga recomendar produtos, frameworks e caminhos tecnicos com
base em fontes confiaveis.

---

## Objetivo do Modulo

```txt
documentacao NVIDIA -> documents/chunks -> embeddings -> base consultavel
```

Esse modulo pode reutilizar ingestion, embeddings e RAG, mas com regras e
metadados especificos para conhecimento tecnico NVIDIA.

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| NVIDIA Knowledge V1 | Implementado | Catalogo inicial de tecnologias |
| NVIDIA Knowledge V2 | Em andamento | Ingestao de fontes oficiais |
| NVIDIA Knowledge V3 | Futuro | Metadados tecnicos |
| NVIDIA Knowledge V4 | Futuro | Busca por caso de uso |

---

## NVIDIA Knowledge V1 - Catalogo Inicial

Status:

```txt
implementado
```

Entregaveis:

- entidade `NvidiaTechnology`;
- catalogo inicial de tecnologias;
- categoria, descricao e casos de uso;
- fonte oficial associada;
- contrato publico `NvidiaTechnologyCatalog`;
- rotas `GET /nvidia-knowledge/technologies` e
  `GET /nvidia-knowledge/technologies/{slug}`;
- filtros por categoria e busca textual simples.

Exemplos:

```txt
NVIDIA NIM
NVIDIA NeMo
NVIDIA Triton Inference Server
TensorRT-LLM
RAPIDS
Riva
CUDA
NVIDIA AI Enterprise
MONAI
```

Documento da entrega: `docs/nvidia_knowledge/nvidia_knowledge_v1_catalogo_inicial.md`.

---

## Extensao do catalogo V1 (entregue; nao e uma nova versao)

Status:

```txt
entregue
```

O brief original do case (secao 5.4) lista 16 tecnologias/programas; o
catalogo V1 cobria 10. Foram adicionadas as 8 que faltavam (ver
`docs/diagnostico_case_original_e_novas_prioridades.md`, secao 5):

```txt
NVIDIA Inception     <- prioridade maxima: e o PROGRAMA que o projeto
                         existe para alimentar (atrair/qualificar/nutrir
                         startups para o Inception). Categoria nova:
                         STARTUP_PROGRAM.
NeMo Guardrails       (categoria MODEL_TRAINING, junto com NeMo)
NVIDIA Clara          (categoria HEALTHCARE_AI, junto com MONAI)
cuDF                  (categoria DATA_SCIENCE, junto com RAPIDS)
cuML                  (categoria DATA_SCIENCE, junto com RAPIDS)
NVIDIA Omniverse      (categoria nova: ROBOTICS_SIMULATION)
NVIDIA Isaac          (categoria nova: ROBOTICS_SIMULATION)
NVIDIA Morpheus       (categoria nova: CYBERSECURITY)
```

Extensao de dados em `catalog_data.py` (`INITIAL_NVIDIA_TECHNOLOGIES`),
mesmo formato das 10 entradas que ja existiam, mais 3 valores novos em
`NvidiaTechnologyCategory` (`STARTUP_PROGRAM`, `ROBOTICS_SIMULATION`,
`CYBERSECURITY`) — sem mudanca de arquitetura nem migration (o catalogo e
estatico em codigo, nao tabela). Por isso fica registrado aqui como
extensao da V1, nao como V2 (que e sobre ingestao de documentacao real
via pipeline, um escopo bem maior — ver abaixo).

Testes novos: `test_catalog_includes_nvidia_inception_program`,
`test_catalog_includes_all_brief_items_added_this_round` (+2, total do
modulo: 7 unit).

---

## NVIDIA Knowledge V2 - Fontes Oficiais

Status:

```txt
fundacao source_type entregue
ingestao das fontes oficiais pendente
```

Fundacao entregue:

- `documents.source_type` com default `startup_evidence`;
- enum `DocumentSourceType` com `startup_evidence` e `nvidia_knowledge`;
- propagacao ingestion reader -> embeddings -> payload Qdrant;
- filtro opcional `source_type` em busca vetorial, busca lexical,
  `/rag/search` e `/rag/answer`;
- migration `1d3e7f9a2b4c`.

Entregaveis:

- pipeline para documentos NVIDIA;
- registro de URL oficial;
- versionamento de documento;
- chunking de documentacao tecnica.

Proximo passo:

```txt
criar registro de fontes oficiais NVIDIA e acionar scraping/ingestion/embeddings
com source_type="nvidia_knowledge"
```

---

## NVIDIA Knowledge V3 - Metadados Tecnicos

Entregaveis:

- mapear tecnologia para caso de uso;
- maturidade da solucao;
- dependencia de hardware/software;
- perfil de startup recomendado.

---

## NVIDIA Knowledge V4 - Busca por Caso de Uso

Entregaveis:

- perguntar em linguagem natural;
- recuperar tecnologias NVIDIA relevantes;
- explicar fonte e motivo da recuperacao.
