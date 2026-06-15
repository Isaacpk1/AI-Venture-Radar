# Roadmap de Evolucao do Projeto

Este documento mostra o passo a passo recomendado para melhorar o AI Venture Radar a partir do estado atual do projeto.

A ideia e separar bem as etapas para evitar misturar responsabilidades. Primeiro terminamos a base de scraping e validacao, depois evoluimos os agentes, depois criamos a camada de ingestao, depois o banco vetorial/RAG, e por fim a recomendacao de tecnologias NVIDIA.

## 1. Estado Atual

Hoje o projeto ja tem uma base importante pronta.

### Scraping

O modulo de scraping ja chegou em uma versao madura para a primeira fase do sistema.

O que ja existe:

- Arquitetura separada em `domain`, `application` e `infrastructure`.
- Entidades de dominio para jobs, attempts e results.
- Repositorios em PostgreSQL com SQLAlchemy assincrono.
- Migrations com Alembic.
- Worker assincrono para executar scraping fora da API.
- Estrategias de extracao com BeautifulSoup, Playwright e Trafilatura.
- Validacao deterministica de qualidade do conteudo.
- Validacao semantica com Gemini.
- Integracao inicial com o modulo de agents.
- Testes cobrindo boa parte da persistencia, pipeline e validacoes.

Conclusao: o scraping nao precisa ser refeito agora. Ele pode evoluir depois, mas ja serve como base para alimentar as proximas partes do sistema.

### Agents

O modulo de agents ja existe em uma primeira versao.

O que ja existe:

- Um contrato publico para validacao semantica.
- Um agente simples usando Gemini.
- Um adapter conectando o scraping com esse agente.
- Documentacao inicial em `docs/agents`.

Conclusao: o modulo de agents esta no comeco. Ele ainda nao e o sistema multiagente final. A proxima grande evolucao deve acontecer aqui.

## 2. Ordem Recomendada

A ordem recomendada de evolucao e:

1. Evoluir o modulo de agents com LangGraph e LangChain.
2. Criar a camada de ingestao dos dados extraidos.
3. Criar o modelo estruturado de startups.
4. Criar embeddings e banco vetorial com Qdrant.
5. Criar o modulo de RAG.
6. Ingerir conhecimento NVIDIA.
7. Criar o motor de recomendacao.
8. Criar relatorios e briefing executivo.
9. Criar dashboard/API de consulta.
10. Melhorar observabilidade, avaliacoes e producao.

Essa ordem e importante porque cada etapa depende da anterior.

O scraping coleta evidencias.  
A ingestao transforma evidencias em dados limpos.  
O banco vetorial permite busca semantica.  
O RAG consulta evidencias e conhecimento NVIDIA.  
Os agentes raciocinam sobre essas informacoes.  
O motor de recomendacao gera a resposta final.

## 3. Fase 1 - Agents V2 com LangGraph e LangChain

Objetivo:

```txt
transformar o agente simples de validacao em um fluxo agentico estruturado
```

Hoje o agente usa Gemini diretamente via cliente HTTP. Isso funciona para a primeira versao, mas nao e a melhor base para fluxos mais complexos.

A proxima versao deve introduzir:

- LangChain para padronizar o uso de modelos, prompts e outputs estruturados.
- LangGraph para organizar o fluxo do agente como um grafo.
- Estado compartilhado do agente.
- Nos especializados.
- Decisao condicional entre aceitar, rejeitar ou buscar mais fontes.

### Entregaveis

- Dependencias de LangChain/LangGraph adicionadas ao projeto.
- Estrutura interna do modulo `agents` preparada para grafos.
- Um `EvidenceValidationGraph`.
- Estado do grafo, por exemplo `EvidenceValidationState`.
- Nos do grafo:
  - preparar entrada;
  - avaliar evidencia;
  - checar confianca;
  - decidir se precisa de mais fontes;
  - gerar resposta final.
- Testes unitarios do grafo.
- Testes de integracao simulando respostas do modelo.

### Criterio de pronto

Esta fase esta pronta quando o scraping continuar chamando a mesma interface publica de agente, mas por baixo a execucao ja passar por LangGraph.

Isso preserva a arquitetura:

```txt
scraping -> contrato publico do agents -> implementacao LangGraph
```

O scraping nao deve conhecer LangGraph diretamente.

## 4. Fase 2 - Ingestao dos Resultados de Scraping

Objetivo:

```txt
transformar scraping_results em dados preparados para analise
```

O scraping gera conteudo bruto ou semiestruturado. A ingestao deve pegar esse material e preparar para uso pelo restante do sistema.

Essa fase nao deve colocar tudo direto no banco vetorial ainda. Antes disso, precisamos limpar, normalizar e estruturar.

### Entregaveis

- Novo modulo `ingestion`.
- Caso de uso para processar um `scraping_result`.
- Normalizacao de texto.
- Extracao de metadados.
- Separacao entre conteudo principal, links, titulo, descricao e fonte.
- Criacao de registros de evidencia.
- Status de processamento da ingestao.
- Testes de unidade e integracao.

### Criterio de pronto

Esta fase esta pronta quando um resultado do scraper puder ser transformado em uma evidencia limpa, rastreavel e pronta para virar embedding.

## 5. Fase 3 - Modelo Estruturado de Startups

Objetivo:

```txt
criar uma base relacional para representar startups e suas evidencias
```

Nem tudo deve ir para banco vetorial. Dados estruturados continuam pertencendo ao PostgreSQL.

Exemplos de dados estruturados:

- Nome da startup.
- Site oficial.
- Pais ou regiao.
- Setor.
- Descricao curta.
- Fundadores.
- Rodada de investimento.
- Tecnologias usadas.
- Fontes associadas.
- Nivel de confianca.

### Entregaveis

- Tabelas relacionais para startups e evidencias.
- Migrations Alembic.
- Entidades de dominio.
- Repositorios PostgreSQL.
- Mappers entre entidades e models SQLAlchemy.
- Casos de uso de criacao/atualizacao de startup.

### Criterio de pronto

Esta fase esta pronta quando o sistema conseguir consolidar varias evidencias em uma mesma startup.

## 6. Fase 4 - Embeddings e Banco Vetorial

Objetivo:

```txt
permitir busca semantica sobre evidencias, startups e conhecimento tecnico
```

Aqui entra o Qdrant.

O banco vetorial nao substitui o PostgreSQL. Ele complementa.

PostgreSQL guarda:

- registros estruturados;
- status;
- relacionamentos;
- auditoria;
- resultados do scraping.

Qdrant guarda:

- chunks de texto;
- embeddings;
- metadados para busca semantica;
- referencias para os registros no PostgreSQL.

### Entregaveis

- Modulo de embeddings.
- Estrategia de chunking.
- Colecoes no Qdrant.
- Repositorio vetorial.
- Sincronizacao entre PostgreSQL e Qdrant.
- Testes de busca semantica.

### Criterio de pronto

Esta fase esta pronta quando for possivel fazer uma busca do tipo:

```txt
"startups que usam IA generativa para saude"
```

e receber evidencias relevantes com referencia para a fonte original.

## 7. Fase 5 - RAG

Objetivo:

```txt
responder perguntas usando evidencias recuperadas do banco vetorial
```

RAG significa Retrieval-Augmented Generation. Na pratica, o sistema primeiro busca informacoes relevantes e depois usa o LLM para gerar uma resposta com base nessas fontes.

### Entregaveis

- Modulo `rag`.
- Retriever para Qdrant.
- Montagem de contexto.
- Prompt com citacoes.
- Resposta estruturada.
- Testes com perguntas conhecidas.

### Criterio de pronto

Esta fase esta pronta quando o sistema conseguir responder perguntas sobre startups citando as evidencias usadas.

## 8. Fase 6 - Ingestao de Conhecimento NVIDIA

Objetivo:

```txt
criar uma base de conhecimento sobre tecnologias NVIDIA
```

Para recomendar tecnologias NVIDIA, o sistema precisa conhecer essas tecnologias.

Exemplos:

- NVIDIA Inception.
- NVIDIA NIM.
- NVIDIA NeMo.
- NVIDIA Triton Inference Server.
- TensorRT-LLM.
- RAPIDS.
- Riva.
- CUDA.
- DGX Cloud.

### Entregaveis

- Pipeline de ingestao de documentos NVIDIA.
- Fontes oficiais versionadas.
- Chunking especifico para documentacao tecnica.
- Embeddings no Qdrant.
- Metadados por produto, caso de uso e maturidade.

### Criterio de pronto

Esta fase esta pronta quando o sistema conseguir recuperar tecnologias NVIDIA relevantes para um problema descrito em linguagem natural.

## 9. Fase 7 - Motor de Recomendacao

Objetivo:

```txt
recomendar tecnologias NVIDIA para startups com base em evidencias
```

Essa e uma das partes centrais do produto.

O motor deve cruzar:

- dados estruturados da startup;
- evidencias coletadas;
- busca semantica;
- conhecimento NVIDIA;
- regras de negocio;
- raciocinio do agente.

### Entregaveis

- Caso de uso de recomendacao.
- Modelo de saida padronizado.
- Score de aderencia.
- Justificativa com evidencias.
- Riscos e incertezas.
- Proximas acoes recomendadas.

Exemplo de saida:

```txt
Startup X
Problema detectado: alto custo de inferencia em modelos generativos
Tecnologia recomendada: TensorRT-LLM
Motivo: pode otimizar inferencia e reduzir latencia
Evidencias: site oficial, post tecnico, documentacao NVIDIA
Confianca: alta
Proxima acao: avaliar benchmark com workload real
```

### Criterio de pronto

Esta fase esta pronta quando uma startup puder receber recomendacoes explicaveis, com fontes e nivel de confianca.

## 10. Fase 8 - Briefing Executivo

Objetivo:

```txt
gerar uma resposta final clara para tomada de decisao
```

O projeto nao deve entregar apenas dados brutos. Ele deve gerar uma analise util.

### Entregaveis

- Relatorio por startup.
- Ranking de oportunidades.
- Resumo executivo.
- Justificativas com fontes.
- Exportacao futura em PDF ou dashboard.

### Criterio de pronto

Esta fase esta pronta quando o sistema conseguir gerar um briefing que uma pessoa de negocio consiga ler sem precisar entender o pipeline tecnico.

## 11. Fase 9 - Dashboard e API de Consulta

Objetivo:

```txt
permitir visualizar, consultar e auditar o sistema
```

Depois que o backend estiver mais forte, faz sentido criar uma interface.

### Entregaveis

- Endpoints para startups.
- Endpoints para evidencias.
- Endpoints para recomendacoes.
- Tela de jobs de scraping.
- Tela de detalhes da startup.
- Tela de recomendacoes NVIDIA.
- Filtros por setor, confianca e tecnologia.

### Criterio de pronto

Esta fase esta pronta quando for possivel acompanhar o fluxo completo pela interface ou API.

## 12. Fase 10 - Observabilidade e Avaliacoes

Objetivo:

```txt
medir qualidade, custo, velocidade e confiabilidade
```

Sistemas com LLM precisam de avaliacao continua.

### Entregaveis

- Logs estruturados.
- Metricas de tempo por etapa.
- Metricas de custo de LLM.
- Taxa de rejeicao do scraper.
- Taxa de `needs_more_sources`.
- Conjunto fixo de testes de avaliacao.
- Testes de regressao para prompts.

### Criterio de pronto

Esta fase esta pronta quando uma mudanca no prompt, no agente ou no scraper puder ser avaliada antes de ir para producao.

## 13. Fase 11 - Producao

Objetivo:

```txt
preparar o sistema para rodar com estabilidade
```

### Entregaveis

- Docker Compose completo com API, worker, PostgreSQL, Redis e Qdrant.
- Separacao de configuracoes por ambiente.
- Politica de secrets.
- Rate limit.
- Retentativas com backoff.
- Dead letter queue para jobs problematicos.
- Health checks.
- Deploy inicial.

### Criterio de pronto

Esta fase esta pronta quando o sistema puder rodar continuamente sem depender de execucao manual no terminal.

## 14. Prioridade Imediata

O proximo passo mais coerente agora e:

```txt
Agents V2 com LangGraph e LangChain
```

Motivo:

- O scraping ja esta suficiente para alimentar o sistema.
- A validacao semantica ja mostrou onde o agente entra.
- O projeto vai precisar de mais agentes depois.
- LangGraph ajuda a organizar fluxos com decisao, memoria, ferramentas e etapas condicionais.

Depois disso, a ordem mais forte e:

1. Ingestao.
2. Modelo estruturado de startups.
3. Embeddings e Qdrant.
4. RAG.
5. Conhecimento NVIDIA.
6. Recomendacao.

## 15. Visao Resumida

| Fase | Nome | Resultado |
| --- | --- | --- |
| 1 | Agents V2 | Validacao agentica com LangGraph |
| 2 | Ingestao | Conteudo limpo e rastreavel |
| 3 | Startups estruturadas | Base relacional de startups |
| 4 | Vetorial | Busca semantica com Qdrant |
| 5 | RAG | Respostas com evidencias |
| 6 | NVIDIA Knowledge | Base tecnica NVIDIA |
| 7 | Recomendacao | Match startup -> tecnologia NVIDIA |
| 8 | Briefing | Analise executiva |
| 9 | Dashboard/API | Consulta e auditoria |
| 10 | Observabilidade | Qualidade e custo medidos |
| 11 | Producao | Sistema estavel em ambiente real |

## 16. Regra Principal

Sempre que uma nova parte for criada, ela deve respeitar a mesma ideia arquitetural:

```txt
domain -> regras puras
application -> casos de uso e contratos
infrastructure -> banco, APIs externas, LLMs, filas e frameworks
```

Isso evita que o projeto vire um bloco dificil de mudar.

O objetivo nao e apenas fazer funcionar. O objetivo e construir uma base que permita trocar tecnologia, evoluir agentes e manter o sistema entendivel.
