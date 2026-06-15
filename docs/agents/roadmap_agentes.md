# Roadmap dos Agentes

Este documento explica como o modulo de agentes deve evoluir por versoes e quais agentes fazem sentido para o AI Venture Radar.

A regra principal e:

```txt
agente nao faz tudo
agente coordena ferramentas, casos de uso e outros modulos
```

Isso evita criar um "super agente" confuso, dificil de testar e dificil de manter.

## 1. Por que teremos agentes?

O projeto precisa tomar decisoes que nao sao apenas CRUD ou regras simples.

Exemplos:

- decidir se uma fonte realmente fala sobre uma startup;
- perceber quando uma evidencia e fraca;
- pedir mais fontes quando uma pagina nao basta;
- cruzar informacoes de varias fontes;
- comparar problemas de uma startup com tecnologias NVIDIA;
- gerar uma recomendacao explicavel;
- montar um briefing final para tomada de decisao.

Essas tarefas exigem raciocinio, contexto e orquestracao. E ai que entram os agentes.

## 2. O que nao e um agente

Um agente nao deve substituir os modulos do sistema.

Exemplos do que nao queremos:

```txt
agente acessando tabela interna do scraping diretamente
agente salvando qualquer coisa no banco sem passar por caso de uso
agente misturando scraping, ingestao, RAG e recomendacao no mesmo arquivo
agente gigante com toda a regra de negocio dentro do prompt
```

O agente deve chamar contratos publicos e ferramentas bem definidas.

Exemplo correto:

```txt
Evidence Validation Agent
-> chama ferramenta de analise de conteudo
-> chama ferramenta de busca de fontes, quando existir
-> retorna uma decisao estruturada
```

## 3. Tecnologias planejadas

Usaremos:

- LangGraph para organizar fluxos com estado, etapas e decisoes condicionais.
- LangChain para padronizar chamadas de modelo, prompts, tools e outputs estruturados.
- Gemini como primeiro modelo de linguagem.
- PostgreSQL para auditoria e historico de execucao.
- Redis/Dramatiq para execucoes longas em worker, quando necessario.

O scraping nao deve conhecer LangGraph nem LangChain.

O fluxo correto e:

```txt
scraping
-> contrato publico do modulo agents
-> agente implementado com LangGraph/LangChain
```

## 4. Agentes que teremos

Nem todos serao criados agora. Esta e a lista planejada para o projeto completo.

### 4.1 Evidence Validation Agent

Responsabilidade:

```txt
validar se uma evidencia coletada pelo scraper e confiavel, relevante e suficiente
```

Ele responde perguntas como:

- esse texto realmente fala da startup?
- a fonte parece oficial ou confiavel?
- o conteudo e suficiente?
- devemos aceitar, rejeitar ou buscar mais fontes?

Status:

```txt
ja existe uma versao inicial simples usando Gemini
proxima versao deve usar LangGraph e LangChain
```

Esse e o primeiro agente porque o scraping ja tem o ponto exato onde ele entra.

### 4.2 Search Planner Agent

Responsabilidade:

```txt
planejar quais buscas devem ser feitas para encontrar evidencias melhores
```

Ele deve decidir termos de busca como:

- nome da startup + site oficial;
- nome da startup + funding;
- nome da startup + founders;
- nome da startup + AI;
- nome da startup + NVIDIA;
- nome da startup + product.

Ele nao deve executar scraping diretamente. Ele deve gerar um plano de busca.

Status:

```txt
futuro
entra depois que o fluxo de needs_more_sources estiver melhor definido
```

### 4.3 Scraper Coordination Agent

Responsabilidade:

```txt
coordenar novas coletas quando uma evidencia isolada nao for suficiente
```

Ele pode decidir:

- tentar site oficial;
- tentar pagina de imprensa;
- tentar Crunchbase ou fonte publica equivalente;
- tentar busca geral;
- parar por falta de evidencia.

Ele nao deve implementar scraper. Ele coordena o modulo `scraping`.

Status:

```txt
futuro
entra depois do Search Planner Agent
```

### 4.4 Extraction Agent

Responsabilidade:

```txt
extrair informacoes estruturadas a partir de evidencias textuais
```

Exemplos:

- nome da startup;
- descricao;
- setor;
- problema resolvido;
- produto;
- tecnologias citadas;
- clientes;
- fundadores;
- rodada de investimento;
- sinais de uso de IA.

Status:

```txt
futuro
entra depois do modulo de ingestao
```

Observacao importante:

Nem toda extracao precisa ser agentica. Primeiro devemos tentar parser, regras e schemas. O agente entra quando o texto for ambigio ou quando precisar interpretar contexto.

### 4.5 Startup Classifier Agent

Responsabilidade:

```txt
classificar a startup por setor, maturidade, tipo de IA e potencial de aderencia
```

Ele pode classificar:

- healthtech;
- fintech;
- devtools;
- cybersecurity;
- industrial AI;
- generative AI;
- robotics;
- edge AI.

Tambem pode identificar sinais como:

- usa modelo generativo;
- tem problema de inferencia;
- precisa de aceleracao;
- trabalha com video, voz, simulacao ou dados tabulares;
- pode ter aderencia com tecnologias NVIDIA.

Status:

```txt
futuro
entra depois que tivermos startups estruturadas
```

### 4.6 NVIDIA Knowledge Agent

Responsabilidade:

```txt
consultar a base de conhecimento NVIDIA e explicar quais tecnologias podem ajudar
```

Ele deve usar RAG sobre documentos NVIDIA.

Exemplos de conhecimento:

- NVIDIA Inception;
- NVIDIA NIM;
- NVIDIA NeMo;
- NVIDIA Triton Inference Server;
- TensorRT-LLM;
- RAPIDS;
- Riva;
- CUDA;
- DGX Cloud.

Status:

```txt
futuro
entra depois do Qdrant e do RAG
```

### 4.7 Recommendation Agent

Responsabilidade:

```txt
gerar recomendacoes de tecnologias NVIDIA para uma startup
```

Ele cruza:

- dados estruturados da startup;
- evidencias coletadas;
- classificacao da startup;
- conhecimento NVIDIA;
- contexto de negocio;
- riscos e incertezas.

Saida esperada:

```txt
startup
problema detectado
tecnologia NVIDIA recomendada
motivo
evidencias usadas
nivel de confianca
proxima acao recomendada
```

Status:

```txt
futuro
entra depois do RAG e do modelo estruturado de startups
```

### 4.8 Briefing Agent

Responsabilidade:

```txt
transformar analises tecnicas em um briefing executivo
```

Ele deve escrever uma resposta clara para uma pessoa tomar decisao.

Pode produzir:

- resumo da startup;
- por que ela importa;
- nivel de aderencia com NVIDIA;
- tecnologias recomendadas;
- riscos;
- proximas acoes.

Status:

```txt
futuro
entra depois do Recommendation Agent
```

## 5. Ordem de criacao dos agentes

A ordem recomendada e:

| Versao | Agente | Por que entra nessa hora |
| --- | --- | --- |
| Agents V1 | Evidence Validation Agent simples | Ja integrado ao scraping |
| Agents V2 | Evidence Validation Agent com LangGraph | Primeiro grafo real |
| Agents V3 | Search Planner Agent | Necessario para buscar mais fontes |
| Agents V4 | Scraper Coordination Agent | Coordena novas coletas |
| Agents V5 | Extraction Agent | Extrai dados estruturados das evidencias |
| Agents V6 | Startup Classifier Agent | Classifica startups ja estruturadas |
| Agents V7 | NVIDIA Knowledge Agent | Usa RAG sobre conhecimento NVIDIA |
| Agents V8 | Recommendation Agent | Recomenda tecnologias NVIDIA |
| Agents V9 | Briefing Agent | Monta a resposta executiva final |

## 6. Agents V1 - Integracao Inicial

Objetivo:

```txt
permitir que o scraping escale casos ambiguos para um agente simples
```

Estado atual:

- existe contrato publico de validacao de evidencia;
- existe implementacao simples com Gemini;
- scraping chama esse contrato quando a validacao semantica simples nao resolve;
- resultado pode ser `accepted`, `rejected` ou `needs_more_sources`.

Limite da V1:

```txt
nao ha LangGraph real
nao ha LangChain
nao ha memoria de execucao
nao ha agent_worker
nao ha busca ativa por novas fontes
```

## 7. Agents V2 - Evidence Validation com LangGraph

Objetivo:

```txt
transformar a validacao de evidencia em um grafo agentico real
```

Entregaveis:

- instalar LangGraph e LangChain;
- criar estrutura de `graphs/evidence_validation`;
- criar estado do grafo;
- criar nodes pequenos;
- criar roteamento condicional;
- manter o mesmo contrato publico usado pelo scraping;
- trocar a implementacao interna sem quebrar o scraping.

Fluxo esperado:

```txt
receber evidencia
-> preparar contexto
-> avaliar relevancia
-> avaliar confianca da fonte
-> avaliar suficiencia
-> decidir accepted/rejected/needs_more_sources
-> retornar resultado estruturado
```

Criterio de pronto:

```txt
o scraping continua chamando a mesma interface
mas por baixo a decisao ja passa por LangGraph
```

## 8. Agents V3 - Search Planner

Objetivo:

```txt
planejar buscas quando o agente de validacao pedir mais fontes
```

Entregaveis:

- contrato publico para plano de busca;
- DTO de entrada com startup, url, texto e motivo da duvida;
- DTO de saida com queries priorizadas;
- grafo simples para gerar e ranquear buscas;
- testes com casos de startup real.

Criterio de pronto:

```txt
quando uma evidencia for insuficiente, o sistema consegue gerar novas buscas plausiveis
```

## 9. Agents V4 - Scraper Coordination

Objetivo:

```txt
coordenar novas tentativas de scraping a partir de um plano de busca
```

Entregaveis:

- tool para criar novos jobs de scraping;
- decisao de limite de tentativas;
- estrategia para evitar loop infinito;
- registro de quais fontes ja foram tentadas;
- integracao com worker.

Criterio de pronto:

```txt
o sistema consegue sair de needs_more_sources e criar novas coletas controladas
```

## 10. Agents V5 - Extraction

Objetivo:

```txt
extrair dados estruturados das evidencias aceitas
```

Entregaveis:

- schema de extracao;
- prompt estruturado;
- validacao de saida;
- ligacao com o futuro modulo de ingestion/startups;
- testes com textos variados.

Criterio de pronto:

```txt
uma evidencia aceita consegue gerar dados estruturados com nivel de confianca
```

## 11. Agents V6 - Startup Classifier

Objetivo:

```txt
classificar startups com base nos dados estruturados e evidencias
```

Entregaveis:

- taxonomia inicial de setores;
- classificacao de tipo de IA;
- identificacao de sinais tecnicos;
- score de maturidade;
- justificativa com evidencias.

Criterio de pronto:

```txt
uma startup estruturada recebe classificacoes explicaveis
```

## 12. Agents V7 - NVIDIA Knowledge

Objetivo:

```txt
usar RAG para consultar conhecimento NVIDIA
```

Entregaveis:

- integracao com modulo RAG;
- queries semanticas sobre Qdrant;
- resposta com citacoes;
- resumo tecnico da tecnologia encontrada.

Criterio de pronto:

```txt
o agente consegue explicar quais tecnologias NVIDIA se conectam a um problema
```

## 13. Agents V8 - Recommendation

Objetivo:

```txt
recomendar tecnologias NVIDIA para startups
```

Entregaveis:

- fluxo LangGraph de recomendacao;
- uso de dados da startup;
- uso de evidencias;
- uso de conhecimento NVIDIA;
- score de aderencia;
- justificativa;
- riscos;
- proximas acoes.

Criterio de pronto:

```txt
uma startup recebe recomendacoes NVIDIA com fontes e confianca
```

## 14. Agents V9 - Briefing

Objetivo:

```txt
gerar uma analise final clara e executiva
```

Entregaveis:

- briefing por startup;
- ranking de oportunidades;
- formato pronto para API ou dashboard;
- linguagem clara para negocio.

Criterio de pronto:

```txt
o sistema consegue entregar uma resposta final compreensivel para tomada de decisao
```

## 15. Como decidir se algo merece virar agente

Antes de criar um novo agente, responder:

1. Essa tarefa precisa de varias etapas?
2. Ela precisa tomar decisoes condicionais?
3. Ela precisa chamar ferramentas diferentes?
4. Ela precisa lidar com incerteza?
5. Ela precisa manter estado?
6. Ela seria ruim se fosse apenas uma funcao comum?

Se a maioria das respostas for "sim", faz sentido criar um agente.

Se for apenas transformar dados de A para B, provavelmente deve ser um service, use case ou mapper.

## 16. Proximo passo imediato

O proximo passo recomendado e:

```txt
Agents V2 - Evidence Validation com LangGraph e LangChain
```

Vamos manter a mesma entrada e saida que o scraping ja usa.

Assim, a evolucao fica segura:

```txt
antes:
scraping -> GeminiEvidenceValidator direto

depois:
scraping -> contrato publico -> EvidenceValidationGraph -> Gemini via LangChain
```

O comportamento externo continua igual, mas a arquitetura interna fica pronta para crescer.
