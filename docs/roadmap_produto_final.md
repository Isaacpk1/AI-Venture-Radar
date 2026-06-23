# Roadmap para Fechar o Produto

Atualizado em 22/06/2026 a partir da revisao cruzada de codigo, testes e
documentacao. Este documento prioriza o que falta para transformar o backend
atual em um produto utilizavel, operavel e apresentavel.

## Diagnostico resumido

O backend possui scraping, ingestao, embeddings, RAG, catalogo NVIDIA,
startups, recomendacoes, briefings, workers e oito agentes LangGraph. A suite
local passou com 443 testes. Ainda nao existe uma experiencia de produto
completa nem uma jornada unica da URL ate o briefing.

## P0 — Jornada funcional de ponta a ponta

### 1. Fechar Orchestration V2

Implementar:

- criar ou associar uma `Startup` ao concluir a ingestao de uma URL;
- anexar evidencias rastreaveis ao perfil;
- executar extract e classify;
- gerar recommendations e briefing;
- persistir o estado, IDs downstream e erro de cada etapa;
- expor consulta agregada do job para polling do frontend;
- garantir idempotencia e retomada segura.

**Pronto quando:** uma URL de startup produz briefing e recomendacoes sem
operacao manual entre as etapas.

### 2. Frontend operacional

Telas minimas:

- submissao de URL e criacao manual de startup;
- acompanhamento de pipeline e erros;
- evidencias, perfil estruturado e classificacao;
- recomendacoes e briefing com citacoes;
- tela de revisao humana e retomada de casos pendentes.

O backend deve receber endpoints de listagem, busca e paginacao consistentes,
incluindo startups e jobs de URL, para suportar essas telas.

## P1 — Qualidade da decisao

### 3. Completar NVIDIA Knowledge V2

- repetir as seis fontes P0 ainda nao validadas;
- executar os lotes P1 e P2;
- medir sucesso de scraping, qualidade de chunks, recuperacao RAG e custo;
- registrar falhas por dominio e estrategia de retry.

### 4. Recommendations V2/V4

- buscar contexto NVIDIA via RAG com citacoes;
- incorporar `ai_maturity_level` ao score;
- adicionar prioridade, confianca, complexidade, proxima acao e trade-offs;
- separar justificativa de negocio da justificativa tecnica;
- integrar Recommendation Agent V11 ao caminho principal quando aplicavel.

### 5. Briefing e revisao

- integrar Briefing Agent V12 ao fluxo principal quando aplicavel;
- exportar HTML/PDF preservando citacoes;
- aprovar/rejeitar, comentar e manter historico de revisao;
- ranquear oportunidades e gerar visao de lote.

## P2 — Prontidao de producao

- autenticacao, autorizacao e isolamento por usuario/organizacao;
- CORS configuravel, rate limiting e controles de abuso;
- logs estruturados, correlation IDs, metricas, tracing, alertas e monitoramento
  de custo/latencia de LLM;
- CI com testes, verificacao de migrations e analise estatica;
- Dockerfiles e compose/manifestos para API e todos os workers;
- backups, retencao de dados, limpeza de checkpoints e plano de rollback;
- documentacao de operacao, variaveis de ambiente e runbooks.

## P3 — Apresentacao do case

- escolher e documentar o diferencial: rastreabilidade ponta a ponta, hibrido
  deterministico/agente por excecao e cobertura do NVIDIA Inception sao os
  candidatos mais fortes;
- preparar demonstracao com uma startup real e fontes NVIDIA recuperaveis;
- definir metricas de valor: tempo ate briefing, cobertura de evidencias,
  qualidade das recomendacoes e taxa de revisao/aprovacao.

## Pendencias de documentacao e release

- manter este roadmap como fonte de priorizacao;
- atualizar documentos historicos quando uma entrega alterar seu status;
- versionar e aplicar a migration `7d4f2a9c6e83` antes de deployar o codigo que
  usa `scraping_jobs.source_type`;
- manter o README raiz com o caminho de execucao atualizado.
