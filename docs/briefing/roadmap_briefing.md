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
| Briefing V1 | Futuro | Template executivo em Markdown |
| Briefing V2 | Futuro | Briefing gerado por agente |
| Briefing V3 | Futuro | Exportacao PDF/HTML |
| Briefing V4 | Futuro | Revisao humana |
| Briefing V5 | Futuro | Ranking de oportunidades |

---

## Briefing V1 - Template Executivo

Entregaveis:

- estrutura padrao do relatorio;
- resumo da startup;
- evidencias principais;
- recomendacoes NVIDIA;
- riscos e proximas acoes;
- saida em Markdown.

Criterio de pronto:

```txt
o sistema gera um briefing legivel a partir de dados estruturados
```

---

## Briefing V2 - Agente de Briefing

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
