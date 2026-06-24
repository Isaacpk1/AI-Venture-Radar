# Roadmap do Modulo Briefing

O modulo `briefing` transforma analises tecnicas em uma saida executiva clara.

Ele e a camada final do produto: o lugar onde uma pessoa de negocio entende o
que foi encontrado e o que fazer.

---

## Objetivo do Modulo

```txt
startup + evidencias + recomendacoes -> briefing executivo
```

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| Briefing V1 | Implementado | Template executivo em Markdown |
| Briefing V2 | Futuro (agente entregue em Agents V12) | Briefing gerado por agente |
| Briefing V3 | Futuro | Exportacao PDF/HTML |
| Briefing V4 | Futuro | Revisao humana |
| Briefing V5 | Futuro | Ranking de oportunidades |

As prioridades transversais de produto estao consolidadas em
`docs/roadmap_produto_final.md`.

---

## Briefing V1 - Template Executivo

Status:

```txt
implementado
```

Entregaveis:

- entidade `Briefing`;
- regras deterministicas (`domain/policies.py`) para riscos e proximas
  acoes a partir de evidencias e recomendacoes;
- estrutura padrao do relatorio (Resumo, Evidencias Principais,
  Recomendacoes NVIDIA, Riscos, Proximas Acoes);
- contrato publico novo em `recommendations` (`RecommendationsReader`) para
  leitura cross-module;
- `POST /briefings`, `GET /briefings/{id}`, `GET /briefings?startup_id=`;
- saida em Markdown;
- testes unitarios das regras e do caso de uso, teste de persistencia
  PostgreSQL.

Criterio de pronto:

```txt
o sistema gera um briefing legivel a partir de dados estruturados
```

Documento da entrega: `docs/briefing/briefing_v1_template_executivo.md`.

**Extensao decidida em 23/06/2026** (`docs/decisoes_pendentes.md`, secao
2 — "vamos ligar o qdrant com o briefing tambem, quero isso junto, e' uma
arma poderosa"): `GenerateBriefing` vai passar a consultar
`rag/application/public/question_answerer.py` (mesmo contrato que
`recommendations` vai usar, ver `docs/recommendations/roadmap_recommendations.md`
V2) pra fundamentar o briefing em conteudo NVIDIA real, nao so no que ja
esta nas evidencias/recomendacoes. Falta implementar — ver "Ordem de
implementacao recomendada" em `docs/roadmap_produto_final.md`.

**Atualizacao de 24/06/2026:** a extensao foi implementada. O adapter
`RagNvidiaContextGrounder` chama o contrato publico de RAG filtrado por
`source_type=nvidia_knowledge`, adiciona citacoes ao briefing quando houver
contexto e faz fallback para o template deterministico quando nao houver.

---

## Briefing V2 - Agente de Briefing

Status:

```txt
agente entregue (Agents V12, ver docs/agents/agents_v12_briefing_agent.md)
modulo briefing em si continua V1 — sem exportacao/revisao humana/ranking
  (isso e' Briefing V3/V4/V5, ainda futuro)
```

O Briefing Agent (V12) so orquestra o que `briefing` V1 ja entrega — nao
e' a "mesma entrega" que V3/V4/V5, que mudariam o modulo em si.

Decisao de design (ja aplicada): o grafo LangGraph orquestra
`BriefingGenerator` (`application/public/briefing_generator.py`,
contrato publico que ja existe desde Orchestration V1) como tool — nao
reescreve `build_briefing_markdown()` (`domain/policies.py`). LLM entra
so para reescrever a prosa executiva (linguagem de negocio), com
fallback seguro em codigo se a reescrita perder alguma citacao/URL do
template determinístico.

Pre-requisito recomendado (atendido): `Recommendation Agent` (Agents
V11), ja entregue antes deste — um briefing fundamentado em
recomendacoes revisadas produz um documento mais util do que orquestrar
so em cima da V1 pura.

Entregue:

- `BriefingAgentGraph` para gerar briefing (4 nodes);
- fallback de controle de citacoes (extrai URLs, compara original vs
  reescrita, descarta a reescrita se alguma faltar);
- linguagem executiva via `LangChainGeminiBriefingProseRewriter`;
- saida estruturada (`BriefingAgentResult`).

Integracao pendente: o Briefing Agent V12 existe, mas `POST /analysis/jobs`
ainda chama o gerador deterministico V1. A decisao de usar a versao com agente
precisa fazer parte do fechamento da Orchestration V2.

---

## Briefing V3 - Exportacao

Entregaveis:

- exportar HTML;
- exportar PDF;
- preservar citacoes;
- template visual simples.

---

## Briefing V4 - Revisao Humana

Entregaveis:

- status `waiting_review`;
- aprovacao/rejeicao;
- comentarios;
- historico de revisao.

---

## Briefing V5 - Ranking de Oportunidades

Entregaveis:

- comparar varias startups;
- ranquear oportunidades;
- gerar sumario para lote;
- destacar oportunidades de alto fit com NVIDIA.

---

## Tecnologias candidatas (auditoria de codigo, 23/06/2026)

Confirmado em `domain/policies.py::build_briefing_markdown()`: a saida e'
Markdown puro, sem nenhum import de biblioteca de exportacao (reportlab,
weasyprint, etc.) — exportar hoje exige copiar o Markdown manualmente.

| Fraqueza confirmada | Tecnologia/abordagem | Serve a | Esforco |
|---|---|---|---|
| Saida so em Markdown, sem exportacao visual | `weasyprint` + Jinja2 (libs leves, sem servico externo) para HTML -> PDF a partir do mesmo Markdown gerado por `build_briefing_markdown()` | Briefing V3 (Exportacao) | Medio |
| Reescrita de prosa do Briefing Agent V12 ja tem fallback contra perda de URL no Markdown — exportacao precisa do mesmo cuidado | validacao pos-render: extrair URLs do PDF gerado e comparar contra as do Markdown original antes de servir o arquivo, mesmo espirito do fallback que V12 ja aplica | Briefing V3, junto do item acima | Baixo — reusa a logica de extracao de URL que V12 ja tem |

Nao adotar um servico externo de geracao de PDF (ex: API paga de
PDF-as-a-service): `weasyprint` roda no mesmo processo Python, sem
dependencia de rede nova, e o volume (1 briefing por vez, sob demanda) nao
justifica um servico separado.
