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
| Briefing V2 | Futuro | Briefing gerado por agente |
| Briefing V3 | Futuro | Exportacao PDF/HTML |
| Briefing V4 | Futuro | Revisao humana |
| Briefing V5 | Futuro | Ranking de oportunidades |

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

---

## Briefing V2 - Agente de Briefing (= Agents V12)

Mesma entrega que `agents` V12 ("Briefing Agent") — ver
`docs/agents/roadmap_agentes.md`. Registrado nos dois lugares pela mesma
razao de Recommendations V3/Agents V11: e ao mesmo tempo uma versao deste
modulo e um agente novo do modulo `agents`.

Decisao de design: o grafo LangGraph orquestra `BriefingGenerator`
(`application/public/briefing_generator.py`, contrato publico que ja
existe desde Orchestration V1) como tool — nao reescreve
`build_briefing_markdown()` (`domain/policies.py`). LLM entra so para
reescrever a prosa executiva (linguagem de negocio), preservando as
citacoes/evidencias que o template determinístico ja garante.

Pre-requisito recomendado: `Recommendation Agent` (Recommendations V3 /
Agents V11) — um briefing fundamentado em recomendacoes mais ricas
(prioridade, complexidade, proxima acao, justificativa de negocio — ver
Recommendations V4) produz um documento mais util do que orquestrar so em
cima da V1.

Entregaveis:

- grafo LangGraph para gerar briefing;
- controle de citacoes;
- linguagem executiva;
- saida estruturada.

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
