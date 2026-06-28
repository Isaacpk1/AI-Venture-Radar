# Documentação — NVIDIA Startup AI Radar

Índice da documentação. A organização tem duas partes: **`geral/`** (a visão de
sistema) e **uma pasta por módulo** (cada módulo com sua visão geral, roadmap e
histórico de versões).

---

## Visão geral do sistema (`geral/`)

| Documento | O que cobre |
|---|---|
| [`geral/arquitetura_monolito_modular_workers.md`](geral/arquitetura_monolito_modular_workers.md) | Por que monolito modular + workers; camadas, regras de dependência, repositório |
| [`geral/comunicacao_entre_modulos.md`](geral/comunicacao_entre_modulos.md) | Os dois canais (contratos públicos + filas), tabela de contratos, adapters |
| [`geral/fluxo_total.md`](geral/fluxo_total.md) | Jornada ponta a ponta: URL → briefing, orquestração, descoberta, RAG |
| [`geral/stack_e_onde_e_usado.md`](geral/stack_e_onde_e_usado.md) | Cada tecnologia, em que camada/módulo entra e por quê |
| [`geral/estado_atual_e_roadmap_futuro.md`](geral/estado_atual_e_roadmap_futuro.md) | Versão por módulo, o que está pronto, limites e roadmap futuro |
| [`geral/rastreabilidade_tap.md`](geral/rastreabilidade_tap.md) | Matriz TAP → implementação: cada requisito do case com status e evidência |

---

## Módulos

Cada pasta de módulo segue o mesmo padrão:
`visao_geral.md` (importância, fluxo, estrutura de pastas, stack, histórico) +
`roadmap.md` (evolução futura) + `versoes/` (um arquivo por versão entregue).

| Módulo | Visão geral | Roadmap | Versões |
|---|---|---|---|
| Scraping | [visao_geral](scraping/visao_geral.md) | [roadmap](scraping/roadmap.md) | [versoes/](scraping/versoes/) |
| Agents | [visao_geral](agents/visao_geral.md) | [roadmap](agents/roadmap.md) | [versoes/](agents/versoes/) |
| Ingestion | [visao_geral](ingestion/visao_geral.md) | [roadmap](ingestion/roadmap.md) | [versoes/](ingestion/versoes/) |
| Embeddings | [visao_geral](embeddings/visao_geral.md) | [roadmap](embeddings/roadmap.md) | [versoes/](embeddings/versoes/) |
| Startups | [visao_geral](startups/visao_geral.md) | [roadmap](startups/roadmap.md) | [versoes/](startups/versoes/) |
| RAG | [visao_geral](rag/visao_geral.md) | [roadmap](rag/roadmap.md) | [versoes/](rag/versoes/) |
| NVIDIA Knowledge | [visao_geral](nvidia_knowledge/visao_geral.md) | [roadmap](nvidia_knowledge/roadmap.md) | [versoes/](nvidia_knowledge/versoes/) |
| Recommendations | [visao_geral](recommendations/visao_geral.md) | [roadmap](recommendations/roadmap.md) | [versoes/](recommendations/versoes/) |
| Briefing | [visao_geral](briefing/visao_geral.md) | [roadmap](briefing/roadmap.md) | [versoes/](briefing/versoes/) |
| Orchestration | [visao_geral](orchestration/visao_geral.md) | [roadmap](orchestration/roadmap.md) | [versoes/](orchestration/versoes/) |
| Startup Discovery | [visao_geral](startup_discovery/visao_geral.md) | [roadmap](startup_discovery/roadmap.md) | [versoes/](startup_discovery/versoes/) |
| Frontend | [visao_geral](frontend/visao_geral.md) | [roadmap](frontend/roadmap.md) | [versoes/](frontend/versoes/) |

---

## Por onde começar

```txt
Novo no projeto?        geral/arquitetura_monolito_modular_workers.md -> geral/fluxo_total.md
Vai mexer num módulo?   <modulo>/visao_geral.md -> <modulo>/roadmap.md -> <modulo>/versoes/
Quer o estado atual?    geral/estado_atual_e_roadmap_futuro.md
```

> A fonte da verdade operacional (head de migrations, contagem de testes) vive em
> `CLAUDE.md` na raiz do repositório; este índice é o mapa da documentação.
