# Modulo Agents - Arquitetura com LangGraph e LangChain

## 1. Objetivo deste documento

Este documento define a arquitetura desejada para o modulo `agents` do
NVIDIA Startup AI Radar.

Ele registra:

```txt
responsabilidade do modulo
limites entre agentes e outros modulos
papel do LangGraph e do LangChain
estrutura interna recomendada
contratos publicos
estado dos grafos
nodes, routers e tools
persistencia e checkpoints
workers
seguranca, custos e observabilidade
estrategia de testes
ordem recomendada de implementacao
```

O modulo deve crescer por necessidade real. Nao criaremos todos os agentes no
primeiro momento.

---

## 2. Contexto do projeto

O NVIDIA Startup AI Radar deve encontrar startups brasileiras, coletar
informacoes publicas, validar evidencias, classificar maturidade AI-native e
recomendar tecnologias NVIDIA.

Fluxo de alto nivel desejado:

```txt
consulta do usuario
-> planejamento de busca
-> scraping
-> extracao estruturada
-> classificacao da startup
-> validacao de evidencias
-> diagnostico de maturidade
-> RAG NVIDIA
-> recomendacao
-> briefing executivo
```

Nem todas essas etapas devem ser implementadas por agentes.

Regra:

```txt
modulo especializado sabe executar uma operacao
agente decide quando e em qual ordem chamar operacoes
```

---

## 3. Responsabilidade do modulo agents

O modulo `agents` e responsavel por orquestrar fluxos que exigem:

```txt
multiplas etapas
decisoes condicionais
uso coordenado de ferramentas
comparacao de fontes
retentativas controladas
estado duravel
intervencao humana
investigacao com caminhos diferentes
```

Ele nao deve reimplementar:

```txt
scraping tecnico
validacao HTTP
limpeza de documentos
persistencia interna de outros modulos
busca vetorial
reranking
regras do motor de recomendacao
geracao de embeddings
```

Essas capacidades pertencem aos modulos especializados.

---

## 4. Regra arquitetural principal

```txt
LangGraph orquestra.
LangChain integra modelos e tools.
Modulos especializados executam.
Workers processam.
Bancos persistem.
```

Exemplo correto:

```txt
Evidence Validation Agent
-> decide que precisa de outra fonte
-> chama contrato publico do modulo scraping
-> recebe resultado
-> compara evidencias
-> devolve decisao fundamentada
```

Exemplo incorreto:

```txt
Evidence Validation Agent
-> importa BeautifulSoup
-> executa SQL em scraping_results
-> cria embeddings diretamente
```

---

## 5. LangGraph e LangChain

### LangGraph

LangGraph sera usado para modelar os fluxos com estado.

Responsabilidades:

```txt
definir nodes
definir transicoes
definir routers condicionais
preservar estado do fluxo
checkpoint
retry
interrupcao e retomada
human-in-the-loop
limitar ciclos
```

LangGraph nao deve conter toda a regra de negocio dentro dos nodes.

### LangChain

LangChain sera usado nas integracoes de IA quando trouxer valor.

Responsabilidades possiveis:

```txt
modelos de chat
structured output
prompts
tools
mensagens
tracing
integracoes com provedores
```

LangChain nao substitui os contratos dos modulos.

Exemplo:

```txt
tool LangChain
-> adapta um contrato publico do modulo scraping
-> nao importa implementacoes internas do scraper
```

---

## 6. Arquitetura em camadas

O modulo segue a arquitetura em camadas do monolito modular:

```txt
Presentation
-> endpoints para iniciar e consultar investigacoes

Application
-> casos de uso, contratos publicos e coordenacao

Domain
-> entidades, estados, decisoes e regras

Graphs
-> definicoes LangGraph por necessidade

Infrastructure
-> LangChain, Gemini, checkpoints, fila e adaptadores externos

Factories
-> composicao das dependencias concretas
```

Regra de dependencia:

```txt
presentation -> application -> domain
graphs -> application/domain
infrastructure -> application/domain
factories -> conecta todas as partes
worker externo -> factory/application
```

Proibido:

```txt
domain -> LangGraph
domain -> LangChain
domain -> Gemini
graphs -> implementacoes internas de outros modulos
agents -> tabelas internas de scraping, rag ou recommendations
worker -> logica dos agentes
```

---

## 7. Estrutura recomendada

```txt
apps/api/src/modules/agents/
|-- presentation/
|   |-- routes.py
|   `-- schemas.py
|-- application/
|   |-- use_cases/
|   |   |-- start_agent_run.py
|   |   |-- resume_agent_run.py
|   |   `-- get_agent_run.py
|   |-- dto.py
|   |-- ports.py
|   `-- public/
|       `-- semantic_investigator.py
|-- domain/
|   |-- entities.py
|   |-- enums.py
|   |-- exceptions.py
|   |-- policies.py
|   `-- repositories.py
|-- graphs/
|   |-- shared/
|   |   |-- state.py
|   |   |-- nodes.py
|   |   `-- routers.py
|   `-- evidence_validation/
|       |-- state.py
|       |-- nodes.py
|       |-- routers.py
|       |-- graph.py
|       `-- prompts.py
|-- infrastructure/
|   |-- llm/
|   |   `-- gemini_chat_model.py
|   |-- tools/
|   |   |-- scraping_tools.py
|   |   |-- rag_tools.py
|   |   `-- startup_tools.py
|   |-- checkpoints/
|   |   `-- postgres_checkpointer.py
|   |-- database/
|   |   |-- models/
|   |   |-- mappers/
|   |   `-- repositories/
|   `-- queue/
|       `-- dramatiq_agent_dispatcher.py
|-- factories/
|   `-- agent_factory.py
`-- tests/
    |-- unit/
    |-- integration/
    `-- fixtures/

workers/agent_worker/
|-- run.py
`-- tasks.py

packages/prompts/
`-- agents/
```

Essa estrutura e um destino arquitetural. Diretorios devem ser criados apenas
quando uma funcionalidade real precisar deles.

---

## 8. Agentes por necessidade

Nao criaremos uma classe generica gigante chamada `Agent`.

Cada necessidade possui:

```txt
estado proprio
grafo proprio
nodes proprios
routers proprios
contrato de entrada e saida
criterio de conclusao
limites operacionais
testes
```

Agentes previstos:

```txt
Search Planner Agent
Scraper Coordination Agent
Extractor Agent
Startup Classifier Agent
Evidence Validation Agent
NVIDIA RAG Agent
Recommendation Agent
Briefing Agent
```

Ordem inicial:

```txt
1. Evidence Validation Agent
2. Search Planner Agent
3. Startup Classifier Agent
4. NVIDIA RAG Agent
5. Recommendation Agent
6. Briefing Agent
```

O primeiro sera o `Evidence Validation Agent`, pois o scraper ja possui o ponto
de escalonamento para casos semanticamente incertos.

---

## 9. Contratos entre modulos

O modulo agents chama somente contratos publicos.

Exemplo conceitual:

```python
class ScrapingRequester:
    async def request_scraping(self, url: str) -> UUID:
        ...


class ScrapingResultReader:
    async def get_raw_document(self, result_id: UUID):
        ...


class RagSearcher:
    async def search(self, query: str):
        ...
```

O modulo scraping pode conhecer o agents por um contrato pequeno:

```python
class SemanticInvestigator:
    async def investigate(self, input):
        ...
```

Ele nao deve importar:

```txt
graphs
nodes
routers
prompts internos
checkpoints
models LangChain
```

---

## 10. Estado do LangGraph

Cada grafo possui um estado tipado.

O estado deve conter apenas informacoes necessarias para continuar a execucao.

Exemplo conceitual:

```python
class EvidenceValidationState(TypedDict):
    run_id: str
    target_name: str | None
    original_url: str
    original_text: str
    semantic_assessment: dict
    evidence_items: list[dict]
    search_queries: list[str]
    sources_consulted: list[str]
    contradictions: list[str]
    iteration: int
    final_decision: str | None
    final_reason: str | None
```

O estado nao deve carregar:

```txt
clientes HTTP
sessoes SQLAlchemy
objetos de banco nao serializaveis
segredos
chaves de API
implementacoes de tools
```

---

## 11. Nodes

Nodes realizam uma etapa pequena e testavel.

Exemplos do agente de validacao:

```txt
analyze_uncertainty
plan_evidence_search
request_additional_sources
read_scraping_results
compare_evidence
decide_validation
prepare_human_review
```

Um node pode:

```txt
ler estado
chamar um servico ou tool
devolver atualizacoes do estado
```

Um node nao deve:

```txt
controlar o grafo inteiro
executar loops infinitos
importar tabelas de outros modulos
esconder varias responsabilidades
```

---

## 12. Routers e transicoes

Routers escolhem o proximo passo com base no estado.

Exemplo:

```txt
semantic_confidence >= 0.80 e sem contradicao
-> finish_accepted

faltam evidencias e iteracao < limite
-> plan_evidence_search

existem contradicoes importantes
-> human_review

limite de iteracoes atingido
-> finish_needs_more_sources
```

Routers devem ser deterministas sempre que possivel.

A LLM pode sugerir uma acao, mas uma politica do sistema deve validar se a
acao e permitida.

---

## 13. Tools

Tools sao adaptadores usados pelos agentes para chamar capacidades externas.

Exemplos:

```txt
request_scraping_tool
read_scraping_result_tool
search_startup_records_tool
search_nvidia_rag_tool
save_recommendation_tool
```

Regra:

```txt
tool valida entrada
-> chama contrato publico de um modulo
-> devolve saida pequena e estruturada
```

Tools nao devem:

```txt
conter prompts gigantes
executar SQL direto em tabelas de outro modulo
retornar dados sem rastreabilidade
permitir chamadas arbitrarias a URLs internas
```

---

## 14. Prompts

Prompts devem ser versionados fora dos nodes quando crescerem.

Local recomendado:

```txt
packages/prompts/agents/
```

Cada prompt deve registrar:

```txt
objetivo
entrada esperada
saida estruturada
versao
modelo recomendado
exemplos
restricoes
```

O prompt nao deve ser a unica protecao.

Saidas devem ser validadas por:

```txt
Pydantic
enums
politicas
limites
contratos de tools
```

---

## 15. Modelos de linguagem

Gemini e o provedor inicial.

LangChain pode fornecer o adaptador de chat para os agentes:

```txt
ChatGoogleGenerativeAI
structured output
tool calling
mensagens
```

O modulo agents nao deve espalhar configuracoes do Gemini pelos grafos.

Fluxo recomendado:

```txt
AgentFactory
-> cria modelo configurado
-> injeta nos nodes que precisam de IA
```

Configuracoes:

```txt
modelo
temperature
timeout
retries
limite de tokens
structured output
```

---

## 16. Persistencia e checkpoints

LangGraph precisa de checkpoint para fluxos longos ou interrompiveis.

Checkpoint permite:

```txt
retomar depois de falha
aguardar aprovacao humana
auditar estado anterior
evitar recomecar investigacao
```

PostgreSQL e a escolha recomendada para checkpoints duraveis.

Separacao:

```txt
checkpoint LangGraph
-> estado tecnico do grafo

agent_runs
-> estado de negocio consultado pela API

resultados dos modulos
-> continuam pertencendo aos respectivos modulos
```

Tabelas futuras:

```txt
agent_runs
agent_steps
agent_artifacts
```

Nao criaremos essas tabelas antes de definir o primeiro fluxo real.

---

## 17. Jobs e worker

Fluxos longos devem executar fora da API.

```txt
API
-> cria AgentRun
-> publica run_id
-> Redis + Dramatiq
-> agent_worker
-> chama caso de uso do modulo agents
-> LangGraph executa ou retoma
```

O worker:

```txt
recebe identificador
chama factory/caso de uso
nao contem nodes ou regras
```

---

## 18. Human-in-the-loop

Intervencao humana sera usada quando:

```txt
fontes confiaveis se contradizem
identidade da startup continua incerta
acao possui custo elevado
agente pede nova coleta ampla
decisao pode afetar briefing executivo
limite de iteracoes foi atingido
```

Estados possiveis:

```txt
waiting_human_review
approved
rejected
resumed
```

A API deve permitir consultar o motivo da interrupcao antes da aprovacao.

---

## 19. Limites operacionais

Todo grafo precisa definir:

```txt
max_iterations
max_tool_calls
max_sources
max_total_tokens
timeout_total
timeout_por_node
budget_estimado
```

Quando um limite for atingido:

```txt
registrar motivo
preservar checkpoint
encerrar ou solicitar revisao humana
```

Nunca permitir loop aberto controlado somente pela LLM.

---

## 20. Seguranca

Regras:

```txt
segredos somente em variaveis de ambiente
tools com entradas validadas
URLs passam por contratos seguros do scraping
prompt injection tratada como dado nao confiavel
respostas estruturadas validadas
acoes caras ou destrutivas exigem politica
logs nao incluem chaves ou documentos sensiveis completos
```

Conteudo coletado da web nunca deve ser tratado como instrucao do sistema.

---

## 21. Observabilidade

Registrar:

```txt
run_id
graph_name
graph_version
node iniciado e concluido
transicao escolhida
tools chamadas
fontes consultadas
modelo utilizado
tokens
latencia
custo estimado
retries
decisao final
motivo
```

LangSmith pode ser avaliado para tracing, mas nao deve ser obrigatorio para o
funcionamento do sistema.

---

## 22. Testes

### Testes de dominio

```txt
transicoes de AgentRun
politicas de limite
decisoes permitidas
```

### Testes de nodes

```txt
node recebe estado
tool falsa devolve resultado
node atualiza somente os campos esperados
```

### Testes de routers

```txt
cada condicao escolhe a transicao correta
limites encerram ciclos
contradicoes pedem revisao
```

### Testes de grafo

```txt
fluxo feliz
baixa confianca solicita fontes
contradicao interrompe
limite de iteracoes encerra
retomada usa checkpoint
```

### Testes de integracao

```txt
fila executa agent_worker
checkpoint PostgreSQL persiste
tools chamam contratos publicos reais
Gemini devolve structured output
```

Testes unitarios nao devem consumir APIs externas.

---

## 23. Agentes planejados

### Evidence Validation Agent

```txt
investiga evidencias semanticamente incertas
compara fontes
detecta contradicoes
aceita, rejeita ou pede mais fontes
```

### Search Planner Agent

```txt
transforma objetivo em consultas e fontes prioritarias
```

### Extractor Agent

```txt
coordena extracao estruturada quando regras simples nao bastam
```

### Startup Classifier Agent

```txt
classifica AI-native, AI-enabled ou non-AI com evidencias
```

### NVIDIA RAG Agent

```txt
coordena consultas a base NVIDIA com citacoes
```

### Recommendation Agent

```txt
cruza gaps tecnicos com tecnologias NVIDIA
```

### Briefing Agent

```txt
organiza o resultado final para o gerente de Startups e VCs
```

---

## 24. Ordem recomendada de implementacao

```txt
1. documentar arquitetura do modulo
2. criar estrutura minima do modulo agents
3. instalar LangGraph e LangChain
4. definir AgentRun e contratos publicos
5. implementar Evidence Validation Agent
6. criar agent_worker
7. adicionar checkpoint PostgreSQL
8. integrar com scraping por contrato publico
9. adicionar human-in-the-loop
10. medir tokens, custo e latencia
11. criar novos agentes somente por necessidade
```

---

## 25. Criterio da primeira versao

A primeira versao do modulo agents estara concluida quando:

```txt
Evidence Validation Agent possuir grafo LangGraph real
nodes e routers forem pequenos e testados
Gemini for acessado por adaptador LangChain
tools chamarem contratos publicos
estado possuir checkpoint duravel
worker executar o grafo fora da API
baixa confianca e contradicao forem tratadas
decisao final possuir fontes e justificativa
```

---

## 26. Regra final

```txt
Agente nao e um modulo especialista.
Agente coordena especialistas.

LangGraph nao e a regra de negocio.
LangGraph organiza o fluxo da regra.

LangChain nao e a arquitetura.
LangChain adapta modelos e ferramentas.
```
