# Roadmap do Modulo Recommendations

O modulo `recommendations` cruza perfil de startup, evidencias e conhecimento
NVIDIA para gerar recomendacoes explicaveis.

Ele nao deve apenas "chutar uma tecnologia". Ele deve justificar com fontes.

---

## Objetivo do Modulo

```txt
startup + evidencias + conhecimento NVIDIA -> recomendacoes explicaveis
```

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| Recommendations V1 | Futuro | Regras deterministicas iniciais |
| Recommendations V2 | Futuro | Recomendacao com RAG |
| Recommendations V3 | Futuro | Agent Recommendation |
| Recommendations V4 | Futuro | Ranking e confianca |
| Recommendations V5 | Futuro | Feedback humano |

---

## Recommendations V1 - Regras Deterministicas

Entregaveis:

- entidade `Recommendation`;
- regras simples por setor/caso de uso;
- score inicial de aderencia;
- justificativa simples;
- testes unitarios das regras.

Criterio de pronto:

```txt
uma startup com perfil estruturado recebe recomendacoes iniciais rastreaveis
```

---

## Recommendations V2 - Recomendacao com RAG

Entregaveis:

- consultar evidencias da startup;
- consultar conhecimento NVIDIA;
- montar contexto;
- gerar recomendacao com citacoes.

---

## Recommendations V3 - Agent Recommendation

Entregaveis:

- grafo LangGraph para recomendacao;
- nodes para analisar perfil, buscar conhecimento e justificar;
- contrato publico para executar recomendacao;
- AgentRun associado.

---

## Recommendations V4 - Ranking e Confianca

Entregaveis:

- score por tecnologia;
- nivel de confianca;
- riscos e incertezas;
- explicacao de tradeoffs.

---

## Recommendations V5 - Feedback Humano

Entregaveis:

- aprovar/rejeitar recomendacoes;
- registrar feedback;
- usar feedback em avaliacoes futuras.
