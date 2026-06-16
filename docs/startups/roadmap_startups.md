# Roadmap do Modulo Startups

O modulo `startups` representa empresas, evidencias associadas e dados
estruturados usados para classificacao e recomendacao.

Ele nao faz scraping, nao gera embeddings e nao recomenda tecnologias sozinho.
Ele organiza a base relacional das startups.

---

## Objetivo do Modulo

```txt
consolidar varias evidencias em uma representacao estruturada de startup
```

---

## Versoes Planejadas

| Versao | Status | Objetivo |
|---|---|---|
| Startups V1 | Futuro | Modelo relacional basico |
| Startups V2 | Futuro | Consolidacao de evidencias |
| Startups V3 | Futuro | Classificacao de maturidade em IA |
| Startups V4 | Futuro | Auditoria e confianca |

---

## Startups V1 - Modelo Relacional Basico

Entregaveis:

- entidade `Startup`;
- entidade `StartupEvidence`;
- migration para `startups` e `startup_evidences`;
- repositorios PostgreSQL;
- casos de uso para criar, buscar e atualizar startup;
- testes de persistencia.

Criterio de pronto:

```txt
o sistema consegue cadastrar uma startup e associar evidencias aprovadas
```

---

## Startups V2 - Consolidacao de Evidencias

Entregaveis:

- deduplicar startups por nome/site;
- associar multiplas fontes a mesma startup;
- registrar origem de cada campo;
- manter confianca por evidencia.

---

## Startups V3 - Classificacao de Maturidade em IA

Entregaveis:

- classificar setor;
- classificar tipo de uso de IA;
- estimar maturidade tecnica;
- registrar justificativa com fontes.

---

## Startups V4 - Auditoria e Confianca

Entregaveis:

- historico de alteracoes;
- score de confianca por campo;
- trilha de evidencias;
- suporte a revisao humana futura.
