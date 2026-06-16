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
| NVIDIA Knowledge V1 | Futuro | Catalogo inicial de tecnologias |
| NVIDIA Knowledge V2 | Futuro | Ingestao de fontes oficiais |
| NVIDIA Knowledge V3 | Futuro | Metadados tecnicos |
| NVIDIA Knowledge V4 | Futuro | Busca por caso de uso |

---

## NVIDIA Knowledge V1 - Catalogo Inicial

Entregaveis:

- entidade `NvidiaTechnology`;
- catalogo inicial de tecnologias;
- categoria, descricao e casos de uso;
- fonte oficial associada quando existir.

Exemplos:

```txt
NVIDIA NIM
NVIDIA NeMo
NVIDIA Triton Inference Server
TensorRT-LLM
RAPIDS
Riva
CUDA
DGX Cloud
```

---

## NVIDIA Knowledge V2 - Fontes Oficiais

Entregaveis:

- pipeline para documentos NVIDIA;
- registro de URL oficial;
- versionamento de documento;
- chunking de documentacao tecnica.

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
