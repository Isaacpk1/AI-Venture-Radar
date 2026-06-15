# Validacao de Mensagens e Interacoes entre Modulos

Este documento valida como as mensagens e interacoes entre modulos estao funcionando no monolito modular.

Validacao feita em 15/06/2026.

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
correto como contrato de mensagem
parcial como execucao completa
```

Parcial porque ainda falta `agent_runs` no PostgreSQL. Sem `agent_runs`, o worker recebe o `run_id`, mas ainda nao tem de onde carregar `agent_name`, entrada, status e resultado.

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

Os detalhes devem ficar no banco:

```txt
agent_runs.agent_name
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
24 passed
154 passed
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

O proximo passo necessario e criar persistencia de `agent_runs`, porque ai o `agent_worker` podera transformar `run_id` em execucao real do grafo.
