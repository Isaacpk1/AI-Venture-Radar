# Validacao de Mensagens e Interacoes entre Modulos

Este documento valida como as mensagens e interacoes entre modulos estao funcionando no monolito modular.

Validacao atualizada em 16/06/2026.

## 1. Regra Principal

No monolito modular, os modulos podem conversar, mas nao devem atravessar a fronteira interna uns dos outros.

Regra:

```txt
modulo A chama contrato publico do modulo B
modulo A nao importa implementation interna do modulo B
```

Para workers e filas:

```txt
fila transporta identificadores
worker recebe identificador
worker chama caso de uso do modulo
modulo busca dados completos no banco
```

## 2. Tipos de Interacao

Hoje existem tres tipos principais de interacao.

### 2.1 Chamada direta por contrato publico

Exemplo:

```txt
scraping -> agents
```

Arquivo:

```txt
apps/api/src/modules/scraping/infrastructure/agent_adapters/agents_semantic_investigator.py
```

O scraping nao chama grafo, prompt ou Gemini diretamente. Ele chama:

```txt
agents/application/public/semantic_investigator.py
```

Isso esta correto.

### 2.2 Mensagem por fila

Exemplo:

```txt
API/modulo -> Redis/Dramatiq -> worker
```

O padrao correto e enviar mensagem pequena.

Scraping envia:

```txt
job_id
```

Agents envia:

```txt
run_id
```

Isso esta correto.

### 2.3 Infraestrutura compartilhada

O broker Dramatiq agora mora em:

```txt
apps/api/src/shared/queue/dramatiq_broker.py
```

Isso esta correto porque o broker nao pertence ao scraping nem aos agents. Ele e uma infraestrutura compartilhada.

## 3. Validacao do Scraping

Mensagem enviada para fila:

```txt
job_id
```

Fila:

```txt
scraping
```

Worker:

```txt
workers/scraper_worker
```

Actor:

```txt
execute_scraping_job(job_id)
```

O worker chama:

```txt
ScrapingFactory.create_execute_scraping_job()
```

Status:

```txt
correto
```

## 4. Validacao dos Agents

Mensagem enviada para fila:

```txt
run_id
```

Fila:

```txt
agents
```

Worker:

```txt
workers/agent_worker
```

Actor:

```txt
execute_agent_job(run_id)
```

O worker chama:

```txt
AgentsFactory.create_execute_agent_job()
```

Status:

```txt
correto
```

Na V5, o worker ja executa o grafo real por `agent_type`. A mensagem continua
pequena (`run_id`) e o modulo `agents` busca o restante no PostgreSQL.

## 5. O que foi ajustado

Antes, a mensagem de agents carregava:

```txt
run_id
agent_name
payload
```

Isso funcionava, mas nao era o melhor padrao para o monolito modular, porque `payload` pode crescer e virar dado de negocio trafegando pela fila.

Agora a mensagem carrega somente:

```txt
run_id
```

Os detalhes agora ficam no banco:

```txt
agent_runs.agent_type
agent_runs.input_payload
agent_runs.status
agent_runs.output_payload
agent_runs.error_message
```

## 6. Validacao por Testes

Comandos executados:

```txt
.\venv\Scripts\python.exe -m pytest apps\api\src\modules\agents\tests -q
.\venv\Scripts\python.exe -m pytest apps\api\src\modules -q
```

Resultados:

```txt
37 passed
167 passed
```

## 7. Conclusao

O jeito atual das mensagens esta certo:

```txt
scraping -> fila com job_id
agents   -> fila com run_id
```

O jeito atual das interacoes entre modulos tambem esta certo:

```txt
scraping conhece contrato publico de agents
scraping nao conhece grafo interno de agents
workers chamam factories/casos de uso
broker compartilhado fica em shared
```

O `agent_worker` ja executa o grafo real a partir do `agent_type` persistido em
`agent_runs`. O proximo passo natural em agents e adicionar checkpoint do
LangGraph no PostgreSQL para permitir retomada de grafos e human-in-the-loop.
