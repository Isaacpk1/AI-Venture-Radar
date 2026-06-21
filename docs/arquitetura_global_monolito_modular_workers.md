# Arquitetura Global do Projeto — Monolito Modular Evolutivo + Workers Separados

> Atualizacao em 21/06/2026: este documento descreve a arquitetura alvo e
> alguns exemplos historicos. O estado real atual ja inclui `scraping`,
> `agents`, `ingestion`, `embeddings`, `startups` e `rag`. O proximo bloco de
> produto e `NVIDIA Knowledge V1`. Para a fotografia operacional atual, leia
> `docs/estado_atual_do_projeto.md`.

## Estado atual da arquitetura

Implementado:

```txt
FastAPI
PostgreSQL
Redis/Dramatiq
Qdrant
scraping + scraper_worker
agents V7 + agent_worker
ingestion + ingestion_worker
embeddings + embedding_worker
startups V1
rag V2
```

Ainda pendente:

```txt
nvidia_knowledge
recommendations
briefing
orquestracao end-to-end
frontend
auth/usuarios
observabilidade de producao
```

Fluxo RAG implementado:

```txt
POST /rag/answer
  -> buscar evidencias com RAG V1
  -> montar contexto
  -> chamar LLM
  -> retornar resposta com citacoes estruturadas
```

## 1. Objetivo deste documento

Este documento descreve apenas a arquitetura global do sistema.

Ele apresenta:

```txt
os componentes principais
os módulos existentes
a responsabilidade geral de cada módulo
como os componentes se comunicam
como funcionam API, fila e workers
como os bancos de dados participam do fluxo
como o sistema pode evoluir
```

Este documento não define:

```txt
estrutura interna de pastas dos módulos
arquitetura em camadas dentro de cada módulo
classes internas
services específicos
repositories específicos
validators específicos
strategies específicas
implementações detalhadas
```

Cada módulo deve possuir sua própria documentação técnica em arquivos separados.

Exemplo:

```txt
docs/
├── architecture.md
├── modules/
│   ├── scraping.md
│   ├── ingestion.md
│   ├── startups.md
│   ├── rag.md
│   ├── agents.md
│   └── recommendations.md
│
├── database.md
├── workers.md
└── api.md
```

---

# 2. Visão geral da arquitetura

A arquitetura recomendada é:

```txt
frontend separado
+
API central em FastAPI
+
monolito modular evolutivo
+
workers executados em processos separados
+
fila para tarefas assíncronas
+
PostgreSQL como fonte da verdade
+
Qdrant para busca vetorial
```

Visão simplificada:

```txt
Usuário
↓
Frontend
↓
API
↓
Módulos do backend
↓
PostgreSQL / Qdrant
```

Para tarefas demoradas:

```txt
Frontend
↓
API
↓
Módulo cria um job
↓
Fila
↓
Worker externo
↓
Módulo executa a lógica
↓
Banco é atualizado
↓
Frontend consulta o resultado
```

A ideia é começar com um único backend organizado em módulos, sem introduzir microserviços antes de existir uma necessidade real.

---

# 3. Princípios centrais

A arquitetura deve respeitar as seguintes regras:

```txt
O frontend conversa somente com a API.

A API recebe requisições e encaminha operações para os módulos.

Cada módulo possui uma responsabilidade de negócio clara.

Os módulos não acessam livremente os detalhes internos uns dos outros.

Workers são processos externos ao monolito, mas reutilizam a lógica dos módulos.

A fila desacopla a API das tarefas demoradas.

PostgreSQL é a fonte da verdade.

Qdrant é especializado em recuperação vetorial.

LangGraph orquestra fluxos, mas não substitui os módulos.

Prompts e configurações globais são versionados e centralizados.
```

Regra resumida:

```txt
Frontend solicita.
API coordena.
Módulo sabe fazer.
Fila distribui.
Worker executa.
Banco persiste.
Agente orquestra.
```

---

# 4. Estrutura global do projeto

```txt
project/
│
├── apps/
│   ├── web/
│   │   └── src/
│   │
│   └── api/
│       └── src/
│           ├── main.py
│           │
│           ├── modules/
│           │   ├── scraping/
│           │   ├── ingestion/
│           │   ├── startups/
│           │   ├── rag/
│           │   ├── agents/
│           │   └── recommendations/
│           │
│           ├── database/
│           │   ├── relational/
│           │   └── vector/
│           │
│           ├── shared/
│           └── config/
│
├── workers/
│   ├── scraper_worker/
│   ├── ingestion_worker/
│   ├── embedding_worker/
│   └── agent_worker/
│
├── packages/
│   ├── shared/
│   └── prompts/
│
├── infra/
│   └── docker-compose.yml
│
├── docs/
├── .env
├── .gitignore
└── README.md
```

Essa árvore mostra apenas os grandes blocos da aplicação.

A estrutura interna de cada módulo deve ser explicada em seu próprio documento.

---

# 5. Componentes principais

## 5.1 Frontend

Local:

```txt
apps/web/
```

Tecnologia sugerida:

```txt
Next.js
TypeScript
Tailwind CSS
TanStack Query
```

Responsabilidades globais:

```txt
receber entradas do usuário
enviar requisições para a API
mostrar status de jobs
mostrar startups analisadas
mostrar resultados do scraping
mostrar respostas do RAG
mostrar recomendações
permitir exportação de briefing
```

O frontend não deve acessar diretamente:

```txt
PostgreSQL
Supabase
Qdrant
Redis
workers
LangGraph
chaves de LLM
serviços internos dos módulos
```

Comunicação permitida:

```txt
Frontend → API
```

---

## 5.2 API

Local:

```txt
apps/api/
```

Tecnologia sugerida:

```txt
Python
FastAPI
```

Responsabilidades globais:

```txt
receber requisições HTTP
validar contratos de entrada
autenticar e autorizar usuários
encaminhar operações aos módulos
criar jobs
consultar status
retornar resultados
expor endpoints do sistema
```

A API não deve executar diretamente trabalhos demorados.

Exemplo:

```txt
requisição rápida
→ API pode responder diretamente

scraping pesado
→ API cria job e envia para fila

geração de embeddings
→ API cria job e envia para fila

execução multiagente
→ API cria job e envia para fila
```

---

## 5.3 Monolito modular

O backend principal é um único sistema implantável, mas organizado em módulos independentes por responsabilidade.

```txt
modules/
├── scraping/
├── ingestion/
├── startups/
├── rag/
├── agents/
└── recommendations/
```

Isso significa:

```txt
uma aplicação backend
um processo principal de API
um código-base central
módulos com fronteiras claras
responsabilidades separadas
```

Não significa:

```txt
todo código misturado
todos os módulos acessando qualquer tabela
um service gigante controlando o sistema inteiro
```

---

## 5.4 Workers

Local:

```txt
workers/
```

Workers são processos separados da API.

Eles executam trabalhos demorados recebidos pela fila.

Exemplos:

```txt
scraper_worker
→ executa jobs de scraping

ingestion_worker
→ processa documentos coletados

embedding_worker
→ gera embeddings e atualiza o banco vetorial

agent_worker
→ executa fluxos longos com LangGraph
```

Regra:

```txt
O worker não contém a lógica principal da funcionalidade.
O worker chama o módulo responsável.
```

Exemplo:

```txt
scraper_worker
↓
chama o módulo scraping
↓
módulo scraping executa o caso de uso
```

---

## 5.5 Fila

Tecnologia sugerida:

```txt
Redis + Dramatiq
```

A fila conecta produtores e consumidores de tarefas.

Produtor:

```txt
API ou módulo cria um job
↓
publica uma mensagem na fila
```

Consumidor:

```txt
worker recebe a mensagem
↓
executa a operação
```

A fila deve transportar principalmente identificadores.

Exemplo:

```json
{
  "job_id": "uuid-do-job"
}
```

Evite enviar documentos grandes diretamente pela fila.

O worker deve usar o `job_id` para buscar os dados necessários na fonte adequada.

---

# 6. Módulos do sistema

## 6.1 Módulo `scraping`

Responsabilidade global:

```txt
coletar conteúdo público da web
```

Recebe:

```txt
URL
fonte
contexto da coleta
identificador da startup
```

Produz:

```txt
conteúdo bruto
metadados da fonte
resultado da coleta
status do job
registro das tentativas
```

O módulo pode usar diferentes tecnologias de coleta, fallback e validação, mas esses detalhes pertencem ao documento específico do módulo.

Não é responsabilidade do scraping:

```txt
gerar embeddings
executar RAG
produzir recomendação NVIDIA
```

---

## 6.2 Módulo `ingestion`

Responsabilidade global:

```txt
transformar dados brutos em dados utilizáveis
```

Recebe:

```txt
resultado aprovado do scraping
documentos enviados por outras fontes
```

Executa:

```txt
limpeza
normalização
extração de informações
deduplicação
chunking
preparação para embeddings
```

Produz:

```txt
documentos tratados
dados estruturados
chunks
metadados normalizados
```

Regra:

```txt
Dado bruto não deve ir diretamente para o RAG.
```

---

## 6.3 Módulo `startups`

Responsabilidade global:

```txt
manter a representação principal das startups no sistema
```

Gerencia:

```txt
cadastro da startup
nome
site
setor
descrição
perfil
documentos relacionados
análises relacionadas
recomendações relacionadas
```

Ele funciona como o núcleo do domínio de empresas analisadas.

Outros módulos se relacionam com uma startup por identificadores e contratos definidos.

---

## 6.4 Módulo `rag`

Responsabilidade global:

```txt
recuperar conhecimento e gerar respostas fundamentadas
```

Executa:

```txt
busca lexical
busca vetorial
combinação dos resultados
reranking
montagem de contexto
geração da resposta
citações
```

Fluxo:

```txt
Pergunta
↓
Busca lexical + busca vetorial
↓
Reranking
↓
Contexto
↓
LLM
↓
Resposta com fontes
```

O RAG consome documentos já tratados pelo módulo de ingestion.

---

## 6.5 Módulo `agents`

Responsabilidade global:

```txt
orquestrar fluxos complexos com LangGraph
```

Pode coordenar:

```txt
planejamento de busca
scraping
ingestion
classificação
validação de evidências
RAG
recomendação
geração de briefing
```

O módulo de agentes não deve reimplementar a lógica dos outros módulos.

Regra:

```txt
Agente decide o próximo passo.
Módulo especializado executa a operação.
```

Exemplo:

```txt
Search Agent
↓
chama operação pública do módulo scraping

RAG Agent
↓
chama operação pública do módulo rag

Recommendation Agent
↓
chama operação pública do módulo recommendations
```

---

## 6.6 Módulo `recommendations`

Responsabilidade global:

```txt
gerar recomendações de tecnologias NVIDIA
```

Recebe:

```txt
perfil da startup
dados estruturados
classificação
evidências
contexto recuperado pelo RAG
```

Produz:

```txt
tecnologias recomendadas
prioridade
justificativa técnica
justificativa de negócio
complexidade
próxima ação sugerida
fontes utilizadas
```

---

# 7. Bancos de dados

## 7.1 PostgreSQL ou Supabase

Responsabilidade:

```txt
ser a fonte da verdade do sistema
```

Guarda dados estruturados e registros operacionais.

Exemplos:

```txt
users
startups
sources
documents
chunks
scraping_jobs
scraping_results
ingestion_jobs
embedding_jobs
analysis_jobs
recommendations
agent_runs
rag_queries
status
histórico
metadados
```

Regra:

```txt
Se o dado é importante para consistência, auditoria ou relacionamento,
ele deve existir no PostgreSQL.
```

---

## 7.2 Qdrant

Responsabilidade:

```txt
armazenar vetores e permitir busca semântica
```

Guarda:

```txt
embedding
chunk_id
document_id
startup_id
metadados mínimos de busca
```

O texto original e os dados completos continuam no PostgreSQL.

Regra:

```txt
PostgreSQL guarda a verdade.
Qdrant acelera a recuperação semântica.
```

Todo vetor deve possuir identificadores que apontem para registros reais no banco relacional.

---

# 8. Comunicação entre módulos

Os módulos não devem acessar livremente arquivos internos uns dos outros.

A comunicação deve acontecer por contratos públicos.

Exemplos de mecanismos:

```txt
services públicos
casos de uso públicos
interfaces
DTOs
eventos
fila
IDs compartilhados
```

Exemplo correto:

```txt
ingestion
↓
solicita ao contrato público de scraping
↓
recebe documento bruto aprovado
```

Exemplo incorreto:

```txt
ingestion
↓
importa model interno do banco de scraping
↓
faz consulta direta na tabela interna
```

Regra:

```txt
Um módulo conhece a interface pública do outro,
não sua implementação interna.
```

---

# 9. Fluxo global de scraping e ingestion

```txt
Usuário envia uma URL
↓
Frontend chama a API
↓
API chama o módulo scraping
↓
Scraping cria um job no PostgreSQL
↓
Scraping envia job_id para a fila
↓
Scraper worker recebe job_id
↓
Worker chama o módulo scraping
↓
Scraping coleta e valida o conteúdo
↓
Resultado bruto é salvo no PostgreSQL
↓
Job de scraping é concluído
↓
Ingestion é acionado
↓
Ingestion trata o documento
↓
Dados estruturados e chunks são salvos
```

O acionamento do ingestion pode ocorrer por:

```txt
chamada de um serviço público
evento interno
nova tarefa na fila
```

A escolha pode evoluir com o sistema.

---

# 10. Fluxo global de embeddings

```txt
Ingestion conclui o chunking
↓
Cria embedding_job no PostgreSQL
↓
Envia job_id para a fila
↓
Embedding worker recebe
↓
Worker chama a lógica de embeddings
↓
Embeddings são gerados
↓
Vetores são armazenados no Qdrant
↓
Referências permanecem ligadas aos chunks do PostgreSQL
↓
Job é concluído
```

---

# 11. Fluxo global do RAG

```txt
Usuário faz uma pergunta
↓
Frontend chama a API
↓
API chama o módulo RAG
↓
RAG executa busca lexical no banco relacional
+
RAG executa busca vetorial no Qdrant
↓
Resultados são combinados
↓
Reranker seleciona as melhores evidências
↓
Contexto é enviado ao LLM
↓
Resposta com citações é gerada
↓
API retorna ao frontend
```

---

# 12. Fluxo global de análise da startup

```txt
Usuário solicita análise
↓
API cria analysis_job
↓
Agent worker recebe a tarefa
↓
Módulo agents inicia o grafo
↓
Search Planner define fontes
↓
Scraping coleta dados
↓
Ingestion trata os dados
↓
Startups atualiza o perfil da empresa
↓
RAG recupera conhecimento relevante
↓
Recommendations gera recomendações NVIDIA
↓
Agents organiza o briefing final
↓
Resultado é salvo
↓
Frontend consulta e apresenta
```

---

# 13. Fluxo dos status

Toda tarefa demorada deve possuir um job persistido.

Status mínimos:

```txt
pending
running
completed
failed
```

Opcionalmente:

```txt
cancelled
retrying
partial
blocked
```

Fluxo:

```txt
API cria job
↓
pending

worker inicia
↓
running

execução termina
↓
completed
```

Em caso de erro:

```txt
failed
+
error_message
```

O frontend consulta o status pela API.

O frontend não consulta workers ou filas diretamente.

---

# 14. Responsabilidade por atualizar status

A responsabilidade deve ser organizada assim:

```txt
API ou módulo
→ cria o job como pending

Worker
→ inicia a execução

Módulo executado pelo worker
→ aplica a lógica e atualiza o estado do job

Frontend
→ apenas consulta
```

O worker não deve duplicar as regras de transição de estado.

Ele apenas chama a operação apropriada do módulo.

---

# 15. Comunicação síncrona e assíncrona

## Comunicação síncrona

Use quando a operação é rápida.

Exemplos:

```txt
listar startups
consultar job
buscar resultado salvo
consultar recomendação existente
pergunta RAG simples, quando o tempo for aceitável
```

Fluxo:

```txt
Frontend → API → Módulo → Banco → API → Frontend
```

## Comunicação assíncrona

Use quando a operação pode demorar.

Exemplos:

```txt
scraping
crawling
ingestion de documento grande
geração de embeddings
execução multiagente
geração de briefing completo
```

Fluxo:

```txt
Frontend → API → Job → Fila → Worker → Módulo → Banco
```

---

# 16. Packages compartilhados

## `packages/prompts`

Guarda prompts reutilizados pelo sistema.

Exemplos:

```txt
extraction_prompt.md
semantic_validation_prompt.md
rag_answer_prompt.md
recommendation_prompt.md
briefing_prompt.md
```

Regra:

```txt
Prompts são parte versionada do sistema.
```

## `packages/shared`

Deve conter apenas contratos ou recursos realmente compartilhados entre aplicações ou processos.

Exemplos possíveis:

```txt
tipos de eventos
DTOs de mensagens
identificadores
constantes globais
```

Evite transformar `shared` em um local para qualquer código sem dono.

---

# 17. Shared e config da API

## `shared`

Pode conter recursos usados por vários módulos:

```txt
logger
erros globais
segurança
observabilidade
tipos comuns
utilitários genéricos
```

Se algo pertence somente a um módulo, deve permanecer nesse módulo.

## `config`

Centraliza:

```txt
DATABASE_URL
QDRANT_URL
REDIS_URL
FIRECRAWL_API_KEY
LLM_API_KEY
COHERE_API_KEY
ENVIRONMENT
LOG_LEVEL
```

As variáveis de ambiente não devem ficar espalhadas pelo código.

---

# 18. Infraestrutura

Local:

```txt
infra/
```

Responsável por definir como os serviços são executados.

Pode incluir:

```txt
Docker
Docker Compose
PostgreSQL
Redis
Qdrant
API
frontend
workers
configuração de rede
volumes
health checks
```

Visão de containers:

```txt
web
api
postgres
redis
qdrant
scraper_worker
ingestion_worker
embedding_worker
agent_worker
```

Todos podem pertencer ao mesmo projeto sem serem microserviços de negócio.

Workers separados são processos de execução, não necessariamente microserviços independentes.

---

# 19. Observabilidade global

O sistema deve possuir logs correlacionados por identificadores.

Identificadores importantes:

```txt
request_id
job_id
startup_id
document_id
agent_run_id
```

Exemplo:

```txt
API cria scraping_job
↓
log contém job_id

worker recebe tarefa
↓
log contém o mesmo job_id

módulo salva resultado
↓
log contém o mesmo job_id
```

Métricas úteis:

```txt
quantidade de jobs
tempo médio
taxa de falha
tamanho da fila
taxa de retry
custos de LLM
custos de APIs externas
tempo de scraping
tempo de embeddings
tempo de execução dos agentes
```

---

# 20. Tratamento global de erros

Erros devem ser:

```txt
registrados
associados ao job
convertidos em status controlado
expostos de forma segura pela API
```

Fluxo:

```txt
módulo encontra erro
↓
job é marcado como failed
↓
erro técnico é registrado
↓
API retorna mensagem controlada
↓
frontend mostra estado compreensível
```

Nunca exponha ao frontend:

```txt
stack trace completo
credenciais
tokens
detalhes internos sensíveis
```

---

# 21. Segurança global

Regras:

```txt
segredos apenas em .env ou secret manager
frontend nunca recebe chaves privadas
API valida entradas
scraping protege contra SSRF
rotas sensíveis exigem autorização
logs não armazenam segredos
workers usam as mesmas configurações seguras
banco possui migrations e controle de acesso
```

---

# 22. Evolução da arquitetura

## Fase inicial

```txt
frontend
API
PostgreSQL
módulo scraping
módulo startups
scraper worker
Redis
```

## Segunda etapa

```txt
módulo ingestion
ingestion worker
Qdrant
embedding worker
```

## Terceira etapa

```txt
módulo RAG
busca híbrida
reranking
```

## Quarta etapa

```txt
módulo recommendations
módulo agents
agent worker
LangGraph
briefing final
```

A arquitetura deve crescer junto com funcionalidades reais.

---

# 23. Possível evolução para microserviços

No início:

```txt
uma API
vários módulos internos
workers separados
bancos compartilhados de forma controlada
```

No futuro, um módulo pode ser extraído se houver necessidade comprovada.

Exemplos de motivos:

```txt
escala muito diferente
deploy independente
equipe independente
isolamento de falhas
requisitos específicos de infraestrutura
```

Possível evolução:

```txt
modules/scraping
↓
scraping-service
```

Mas a extração não deve acontecer apenas porque o sistema possui muitos diretórios ou workers.

---

# 24. Primeiro fluxo funcional recomendado

O primeiro fluxo vertical deve ser:

```txt
Frontend recebe uma URL
↓
POST /scraping/jobs
↓
API chama scraping
↓
Job é salvo
↓
Job é enviado à fila
↓
Scraper worker executa
↓
Scraping salva resultado
↓
GET /scraping/jobs/{id}
↓
GET /scraping/results/{id}
↓
Frontend apresenta o conteúdo
```

Esse fluxo valida:

```txt
frontend
API
módulo
fila
worker
banco
status
resultado
```

Depois disso, ingestion e os outros módulos podem ser conectados progressivamente.

---

# 25. Regras para os documentos específicos dos módulos

Cada módulo deve possuir um documento próprio.

Cada documento pode explicar:

```txt
objetivo do módulo
limites da responsabilidade
arquitetura interna
pastas
entidades
casos de uso
services
repositories
validators
fluxos internos
testes
erros
contratos públicos
```

Exemplos:

```txt
docs/modules/scraping.md
docs/modules/ingestion.md
docs/modules/startups.md
docs/modules/rag.md
docs/modules/agents.md
docs/modules/recommendations.md
```

O documento global não deve duplicar esses detalhes.

---

# 26. Diagrama textual da arquitetura

```txt
                         ┌─────────────────┐
                         │    Frontend     │
                         │    Next.js      │
                         └────────┬────────┘
                                  │ HTTP
                                  ▼
                         ┌─────────────────┐
                         │       API       │
                         │     FastAPI     │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
       ┌────────────┐      ┌────────────┐      ┌──────────────┐
       │  Startups  │      │    RAG     │      │    Agents    │
       └────────────┘      └────────────┘      └──────────────┘
              │                   │                   │
              │          ┌────────┴────────┐          │
              │          │                 │          │
              │          ▼                 ▼          │
              │    ┌───────────┐      ┌─────────┐     │
              │    │PostgreSQL │      │ Qdrant  │     │
              │    └───────────┘      └─────────┘     │
              │                                       │
              └───────────────┬───────────────────────┘
                              │
                              ▼
                        ┌───────────┐
                        │   Redis   │
                        │   Fila    │
                        └─────┬─────┘
                              │
            ┌─────────────────┼──────────────────┐
            │                 │                  │
            ▼                 ▼                  ▼
    ┌──────────────┐  ┌───────────────┐  ┌─────────────┐
    │Scraper Worker│  │Embedding Worker│  │Agent Worker │
    └──────┬───────┘  └───────┬───────┘  └──────┬──────┘
           │                  │                  │
           ▼                  ▼                  ▼
     ┌──────────┐       ┌───────────┐      ┌──────────┐
     │ Scraping │       │ Ingestion │      │  Agents  │
     └──────────┘       └───────────┘      └──────────┘
```

O diagrama é conceitual. Um worker sempre chama a lógica do módulo responsável.

---

# 27. Resumo das responsabilidades

```txt
Frontend
→ interface e experiência do usuário

API
→ entrada HTTP e coordenação

Scraping
→ coleta conteúdo público

Ingestion
→ trata e estrutura documentos

Startups
→ mantém o domínio principal das empresas

RAG
→ recupera contexto e responde com evidências

Agents
→ orquestra fluxos complexos

Recommendations
→ recomenda tecnologias NVIDIA

Fila
→ distribui tarefas demoradas

Workers
→ executam tarefas fora da API

PostgreSQL
→ fonte da verdade

Qdrant
→ busca semântica

Packages
→ prompts e contratos compartilhados

Infra
→ execução e configuração dos serviços
```

---

# 28. Regra mais importante

```txt
O documento global explica como as partes conversam.

Os documentos dos módulos explicam como cada parte funciona internamente.
```

Resumo final:

```txt
Frontend chama a API.
API chama módulos ou cria jobs.
Jobs são enviados para a fila.
Workers externos consomem as tarefas.
Workers chamam os módulos responsáveis.
Módulos persistem dados no PostgreSQL.
Ingestion prepara os chunks.
Embeddings são armazenados no Qdrant.
RAG recupera evidências.
Agents orquestram módulos.
Recommendations produz recomendações NVIDIA.
```

Seguindo essas fronteiras, o sistema começa simples, permanece organizado e pode evoluir sem transformar o monolito em uma aplicação acoplada.
