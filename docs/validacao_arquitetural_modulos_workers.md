# Validacao Arquitetural - Modulos e Workers

Este documento valida se o estado atual do sistema esta de acordo com a regra arquitetural principal:

```txt
modulos sabem como fazer
workers executam o trabalho pesado
```

Validacao atualizada em 16/06/2026.

## 1. Regra Arquitetural

A arquitetura desejada nos documentos principais e:

```txt
API
-> cria ou consulta jobs
-> publica mensagem pequena na fila
-> worker consome a mensagem
-> worker chama o modulo responsavel
-> modulo executa a regra, persistencia e integracoes
```

O worker nao deve conter regra de negocio.

O worker deve:

- receber mensagem da fila;
- converter dados serializaveis;
- chamar factory/caso de uso do modulo correto.

O modulo deve:

- conhecer suas regras;
- conhecer seus casos de uso;
- conhecer seus contratos;
- conhecer suas implementacoes de infraestrutura;
- persistir estado quando necessario.

## 2. Estado Atual dos Modulos

Hoje existem dois modulos principais implementados:

```txt
apps/api/src/modules/scraping
apps/api/src/modules/agents
```

### Scraping

Status:

```txt
de acordo
```

O modulo `scraping` possui:

- `domain`;
- `application`;
- `infrastructure`;
- `presentation`;
- `factories`;
- testes unitarios e integrados.

O trabalho pesado de scraping e executado pelo worker:

```txt
workers/scraper_worker
```

O worker chama:

```txt
ScrapingFactory.create_execute_scraping_job()
```

Isso esta correto porque o worker nao implementa scraping diretamente.

### Agents

Status:

```txt
de acordo
```

O modulo `agents` possui:

- contratos publicos;
- DTOs;
- grafo de validacao de evidencia;
- grafo de planejamento de busca;
- integracao Gemini via LangChain;
- dispatcher de jobs de agentes;
- caso de uso para execucao real pelo worker;
- persistencia de `agent_runs` e `agent_steps`.

O worker de agentes existe:

```txt
workers/agent_worker
```

Ele consome a fila:

```txt
agents
```

E chama:

```txt
AgentsFactory.create_execute_agent_job()
```

Isso esta correto: o worker nao implementa grafo, prompt ou regra de negocio.
Ele apenas chama o caso de uso do modulo `agents`, que busca o `AgentRun`
persistido e executa o grafo correto com base em `agent_type`.

## 3. Estado Atual dos Workers

Existem dois workers:

```txt
workers/scraper_worker
workers/agent_worker
```

### scraper_worker

Status:

```txt
de acordo
```

Responsabilidade atual:

```txt
receber job_id
chamar caso de uso do modulo scraping
```

Fila:

```txt
scraping
```

Actor:

```txt
execute_scraping_job
```

### agent_worker

Status:

```txt
de acordo
```

Responsabilidade atual:

```txt
receber run_id
chamar caso de uso do modulo agents
```

Fila:

```txt
agents
```

Actor:

```txt
execute_agent_job
```

O worker nao contem prompt, grafo ou regra de negocio. Isso esta correto.
Na V5, ele ja executa trabalho pesado de agentes de forma indireta:

```txt
recebe run_id
chama AgentsFactory.create_execute_agent_job()
caso de uso busca AgentRun no PostgreSQL
caso de uso reconstroi DTO de entrada
caso de uso executa EvidenceValidationGraph ou SearchPlanningGraph
caso de uso salva output e AgentStep
```

## 4. Ajuste Feito Durante a Validacao

Foi encontrado um problema arquitetural:

```txt
agents importava o broker Dramatiq de scraping.infrastructure
```

Isso funcionava, mas violava a ideia de fronteira entre modulos. O broker Redis/Dramatiq nao pertence ao scraping; ele e infraestrutura compartilhada.

Foi ajustado para:

```txt
apps/api/src/shared/queue/dramatiq_broker.py
```

Agora:

```txt
scraping usa shared.queue.dramatiq_broker
agents usa shared.queue.dramatiq_broker
scraper_worker usa shared.queue.dramatiq_broker
agent_worker usa shared.queue.dramatiq_broker
```

O arquivo antigo:

```txt
apps/api/src/modules/scraping/infrastructure/queue/dramatiq_broker.py
```

foi mantido apenas como reexport de compatibilidade.

## 5. Validacao por Testes

Comando executado:

```txt
.\venv\Scripts\python.exe -m pytest apps\api\src\modules -q
```

Resultado:

```txt
167 passed
```

Existe apenas um warning interno do LangGraph sobre configuracao futura de serializer/cache. Ele nao quebra o sistema.

## 6. O que Esta De Acordo

Esta de acordo:

- workers ficam fora de `apps/api/src/modules`;
- workers consomem filas separadas;
- `scraper_worker` consome `scraping`;
- `agent_worker` consome `agents`;
- workers chamam factories/casos de uso;
- workers nao implementam regra de negocio;
- scraping possui persistencia PostgreSQL real;
- scraping publica jobs pequenos na fila;
- agents publica somente `run_id` na fila;
- agents possui contratos publicos e grafos internos;
- agents possui dispatcher para jobs;
- agents possui persistencia de `agent_runs` e `agent_steps`;
- broker Dramatiq agora esta em `shared`;
- testes passam.

## 7. Estado dos Agents na V5

A fila de agentes transporta somente:

```txt
run_id
```

Isso esta mais alinhado com o monolito modular, porque `agent_type`, entrada e saida devem ficar persistidos em `agent_runs`.

Isso esta correto para a V5, porque o estado completo da execucao fica em
`agent_runs` e `agent_steps`, nao dentro da mensagem da fila.

O `agent_worker` ja executa grafos reais por `agent_type`:

```txt
EVIDENCE_VALIDATION -> EvidenceValidationGraph
SEARCH_PLANNING     -> SearchPlanningGraph
```

## 8. Proximo Ajuste Necessario

Proximo passo recomendado:

```txt
Agents V6 - Checkpoint LangGraph no PostgreSQL
```

Entregaveis:

- salvar checkpoints do LangGraph no PostgreSQL;
- permitir retomada de grafos apos falha;
- preparar human-in-the-loop;
- evoluir auditoria de estado entre nodes.

## 9. Conclusao

O sistema esta coerente com a arquitetura:

```txt
scraping ja esta maduro com worker e persistencia
agents ja tem agent_runs persistidos e worker executando grafos reais por agent_type
```

Portanto, a arquitetura esta no caminho certo. O proximo passo nao deve ser
criar mais agentes ainda sem necessidade. O mais correto e consolidar
checkpoint/retomada dos grafos ou iniciar o modulo de ingestion, dependendo da
prioridade do produto.
