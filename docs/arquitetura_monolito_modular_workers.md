# Arquitetura do Projeto — Monolito Modular Evolutivo + Workers Separados

## 1. Visão geral da arquitetura

A arquitetura recomendada para o projeto é:

```txt
Monolito modular evolutivo
+
workers separados
+
frontend separado
+
banco relacional como fonte da verdade
+
banco vetorial para busca semântica
```

A ideia central é começar simples, mas com organização suficiente para o projeto crescer sem virar bagunça.

A regra principal é:

```txt
A API coordena.
Os módulos organizam a regra de negócio.
Os services executam a lógica principal.
Os repositories acessam o banco.
Os workers executam tarefas pesadas.
O frontend conversa apenas com a API.
```

Essa arquitetura evita começar com microserviços cedo demais, mas deixa o sistema preparado para, no futuro, separar módulos em serviços independentes se for necessário.

---

## 2. Estrutura geral recomendada

```txt
project/
│
├── apps/
│   ├── web/
│   │   └── src/
│   │       ├── app/
│   │       ├── features/
│   │       ├── components/
│   │       ├── services/
│   │       ├── hooks/
│   │       ├── types/
│   │       └── lib/
│   │
│   └── api/
│       └── src/
│           ├── main.py
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
│   │   ├── run.py
│   │   └── tasks.py
│   │
│   ├── embedding_worker/
│   │   ├── run.py
│   │   └── tasks.py
│   │
│   └── agent_worker/
│       ├── run.py
│       └── tasks.py
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

---

## 3. Responsabilidade de cada parte

### 3.1 `apps/web/`

Responsável pelo frontend da aplicação.

Tecnologia recomendada:

```txt
Next.js + TypeScript + Tailwind CSS + TanStack Query
```

Responsabilidades:

```txt
mostrar interface para o usuário
buscar startup
mostrar status de análise
mostrar resultados de scraping
mostrar recomendações
mostrar respostas do RAG
exportar briefing
```

O frontend não deve conhecer detalhes internos do backend.

Ele não deve acessar diretamente:

```txt
PostgreSQL
Qdrant
workers
LangGraph
chaves de LLM
repositories internos
services internos
```

O frontend deve conversar apenas com a API:

```txt
Frontend → FastAPI
```

Exemplo:

```txt
POST /scraping/jobs
GET /scraping/jobs/{id}
GET /scraping/results/{id}
```

---

### 3.2 `apps/api/`

Responsável pelo backend principal.

Tecnologia recomendada:

```txt
Python + FastAPI
```

Responsabilidades:

```txt
receber requisições do frontend
validar entrada
chamar services dos módulos
criar jobs
consultar status
retornar respostas para o frontend
```

A API não deve fazer trabalho pesado diretamente.

Ela deve coordenar o fluxo.

---

### 3.3 `workers/`

Responsável por processos separados que executam tarefas demoradas.

Exemplos de tarefas para workers:

```txt
scraping pesado
geração de embeddings
execução de agentes
processamento de documentos
pipelines longos
```

Workers não devem conter toda a regra de negócio.

Eles devem chamar os services dos módulos.

Regra principal:

```txt
Worker executa.
Módulo sabe fazer.
```

---

### 3.4 `database/relational/`

Responsável pela conexão com o banco relacional.

Tecnologia recomendada:

```txt
PostgreSQL ou Supabase
```

O banco relacional é a fonte da verdade do sistema.

Guarda dados como:

```txt
startups
users
documents
sources
scraping_jobs
scraping_results
recommendations
agent_runs
rag_queries
status
histórico
metadados
```

Regra:

```txt
Se é dado estruturado e importante, vai para PostgreSQL.
```

---

### 3.5 `database/vector/`

Responsável pela conexão com o banco vetorial.

Tecnologia recomendada:

```txt
Qdrant
```

Guarda:

```txt
chunks
embeddings
metadados mínimos de busca
vetores semânticos
```

Regra:

```txt
Qdrant serve para busca semântica.
PostgreSQL serve como fonte da verdade.
```

O Qdrant não substitui o PostgreSQL.

---

### 3.6 `packages/prompts/`

Responsável por guardar prompts versionados.

Exemplo:

```txt
packages/prompts/
├── extraction_prompt.md
├── validation_prompt.md
├── recommendation_prompt.md
└── rag_answer_prompt.md
```

Regra:

```txt
Prompt é parte do sistema e deve ser versionado.
```

Não deixe prompts grandes perdidos dentro do código Python.

---

### 3.7 `infra/`

Responsável por infraestrutura e ambiente.

Exemplo:

```txt
Docker
Docker Compose
configuração de serviços
PostgreSQL
Qdrant
Redis
workers
```

---

### 3.8 `docs/`

Responsável pela documentação técnica do projeto.

Sugestão:

```txt
docs/
├── architecture.md
├── database.md
├── api.md
├── scraping.md
├── rag.md
└── agents.md
```

Regra:

```txt
Toda decisão arquitetural importante deve ser documentada.
```

---

## 4. Regra principal das camadas

A comunicação ideal entre camadas é:

```txt
Frontend
↓
API route/controller
↓
Service
↓
Repository
↓
Banco de dados
```

Para tarefas pesadas:

```txt
Frontend
↓
API
↓
Service cria job
↓
Fila
↓
Worker
↓
Service executa lógica
↓
Repository salva resultado
↓
Frontend consulta status
```

---

## 5. Regras do frontend

### Regra 1 — Frontend só conversa com a API

Certo:

```txt
Frontend → FastAPI
```

Errado:

```txt
Frontend → PostgreSQL
Frontend → Qdrant
Frontend → Worker
Frontend → LangGraph diretamente
```

---

### Regra 2 — Services do frontend fazem chamadas HTTP

Exemplo de estrutura:

```txt
apps/web/src/services/
├── apiClient.ts
├── scrapingApi.ts
├── startupsApi.ts
└── ragApi.ts
```

---

### Regra 3 — Features agrupam funcionalidades

Exemplo:

```txt
apps/web/src/features/scraping/
├── ScrapingForm.tsx
├── ScrapingStatusCard.tsx
└── ScrapingResultView.tsx
```

Regra:

```txt
Se é específico de scraping, fica em features/scraping.
Se é genérico, fica em components.
```

---

## 6. Regras da API

### Regra 1 — Route/controller não faz regra de negócio

Certo:

```python
@router.post('/jobs')
async def create_job(payload: CreateScrapingJobRequest):
    service = ScrapingService()
    return await service.create_job(payload)
```

Errado:

```python
@router.post('/jobs')
async def create_job(payload):
    # 200 linhas de scraping aqui
    # acesso direto ao banco
    # chamada direta ao Playwright
    # geração de embedding
```

Regra:

```txt
Route/controller recebe a requisição e chama service.
```

---

### Regra 2 — `main.py` só inicializa a aplicação

O `main.py` deve:

```txt
criar a instância FastAPI
registrar routers
configurar CORS
configurar middlewares
```

Não deve conter:

```txt
scraping
RAG
recomendação
SQL
lógica de agente
```

Exemplo:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modules.scraping.routes.router import router as scraping_router
from modules.startups.routes.router import router as startups_router
from modules.rag.routes.router import router as rag_router

app = FastAPI(title='NVIDIA Startup AI Radar API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(scraping_router)
app.include_router(startups_router)
app.include_router(rag_router)
```

---

## 7. Regras dos módulos

Cada módulo representa uma área do sistema.

Exemplo:

```txt
modules/
├── scraping/
├── ingestion/
├── startups/
├── rag/
├── agents/
└── recommendations/
```

Regra:

```txt
Cada módulo deve ter responsabilidade clara.
```

---

## 8. Módulo `scraping/`

Responsável por coleta web.

Responsabilidades:

```txt
receber URL
criar job de scraping
executar scraping
escolher estratégia de scraping
validar conteúdo extraído
salvar resultado bruto
consultar status
consultar resultado
```

Não deve fazer:

```txt
RAG
recomendação NVIDIA
autenticação
frontend
```

Estrutura recomendada:

```txt
modules/scraping/
├── routes/
│   ├── router.py
│   ├── jobs_routes.py
│   └── results_routes.py
│
├── services/
│   ├── scraping_service.py
│   └── strategy_selector.py
│
├── repositories/
│   └── scraping_repository.py
│
├── schemas/
│   ├── requests.py
│   └── responses.py
│
├── strategies/
│   ├── base_strategy.py
│   ├── beautifulsoup_strategy.py
│   ├── playwright_strategy.py
│   └── trafilatura_strategy.py
│
├── validators/
│   └── content_quality_validator.py
│
└── tasks/
    └── scraping_tasks.py
```

---

## 9. Módulo `ingestion/`

Responsável pelo tratamento dos dados coletados.

Responsabilidades:

```txt
limpeza
normalização
extração de campos
chunking
preparação para embedding
```

Fluxo:

```txt
raw_html/raw_text
↓
cleaning
↓
normalization
↓
extraction
↓
chunking
```

Regra:

```txt
Dado bruto nunca deve ir direto para RAG.
```

---

## 10. Módulo `rag/`

Responsável pela busca com contexto e geração de respostas.

Responsabilidades:

```txt
busca vetorial
busca lexical
reranking
montagem de contexto
geração de resposta
citações
```

Fluxo ideal:

```txt
pergunta
↓
busca lexical
+
busca vetorial
↓
reranking
↓
contexto
↓
LLM
↓
resposta com citações
```

Regra:

```txt
LLM não deve responder de memória quando deveria usar documentos.
```

---

## 11. Módulo `agents/`

Responsável pela orquestração multiagente.

Responsabilidades:

```txt
LangGraph
estado dos agentes
ferramentas dos agentes
decisão de próximos passos
validação de saídas
execução de fluxos complexos
```

Regra:

```txt
Agente orquestra.
Service executa regra.
Tool conecta agente ao service.
```

Certo:

```txt
SearchAgent usa ScrapingTool
RagAgent usa RagService
RecommendationAgent usa RecommendationService
ValidationAgent usa Validator
```

Errado:

```txt
Um agente gigante que scrapeia, limpa, salva no banco, gera embedding, recomenda e responde.
```

---

## 12. Módulo `recommendations/`

Responsável pelo motor de recomendação.

Responsabilidades:

```txt
analisar startup
identificar necessidades técnicas
calcular score
recomendar tecnologias NVIDIA
gerar justificativa
```

Estrutura possível:

```txt
modules/recommendations/
├── routes.py
├── controller.py
├── service.py
├── rules_engine.py
├── scoring.py
├── repository.py
└── schemas.py
```

---

## 13. Módulo `startups/`

Responsável pelo cadastro principal do domínio.

Responsabilidades:

```txt
criar startup
listar startups
buscar startup
atualizar dados da startup
relacionar documentos
relacionar análises
relacionar recomendações
```

---

## 14. Regras internas de cada módulo

Um módulo pode ter:

```txt
routes/
services/
repositories/
schemas/
models/
strategies/
validators/
tasks/
```

Mas não precisa criar tudo de uma vez.

Regra:

```txt
Só crie uma pasta quando houver mais de um arquivo ou responsabilidade real.
```

Começo simples:

```txt
modules/scraping/
├── routes.py
├── service.py
├── repository.py
└── schemas.py
```

Quando crescer:

```txt
modules/scraping/
├── routes/
├── services/
├── repositories/
└── schemas/
```

---

## 15. Regras das rotas

Se o módulo tiver poucas rotas, use um arquivo único:

```txt
scraping/
└── routes.py
```

Se tiver muitas rotas ou grupos diferentes, use subrotas:

```txt
scraping/
└── routes/
    ├── router.py
    ├── jobs_routes.py
    └── results_routes.py
```

Regra:

```txt
router.py junta subrotas.
jobs_routes.py cuida de jobs.
results_routes.py cuida de resultados.
```

Exemplo certo:

```txt
POST /scraping/jobs
GET /scraping/jobs/{id}
GET /scraping/results/{id}
```

Exemplo errado:

```txt
create_job_routes.py
delete_job_routes.py
update_job_routes.py
get_job_routes.py
```

Isso é separação exagerada.

---

## 16. Regras dos services

O service é onde fica a regra de negócio.

Exemplo:

```txt
ScrapingService
IngestionService
RagService
RecommendationService
AgentService
```

O service pode:

```txt
coordenar fluxo
chamar repository
chamar strategy
chamar validator
chamar outro service se fizer sentido
disparar job
validar regra de negócio
```

O service não deve:

```txt
receber requisição HTTP diretamente
renderizar tela
conter SQL bruto espalhado
ter código excessivamente acoplado ao framework
```

Regra:

```txt
Se é decisão de negócio, fica no service.
```

---

## 17. Regras dos repositories

Repository é a camada de acesso ao banco.

Ele pode:

```txt
insert
select
update
delete
query
buscar por id
listar
salvar status
```

Ele não deve:

```txt
decidir estratégia de scraping
chamar LLM
executar RAG
validar regra de negócio complexa
chamar frontend
```

Regra:

```txt
Service decide.
Repository persiste.
```

---

## 18. Regras dos schemas

Schemas validam entrada e saída.

Use para:

```txt
payload de POST
resposta de endpoint
dados entre camadas
contrato da API
```

Exemplo:

```python
from pydantic import BaseModel, HttpUrl

class CreateScrapingJobRequest(BaseModel):
    url: HttpUrl
    startup_id: str | None = None
```

Regra:

```txt
Dados vindos de fora sempre passam por schema.
```

---

## 19. Regras dos models

Models representam entidades do domínio ou tabelas do banco.

Exemplo:

```txt
Startup
ScrapingJob
Document
Chunk
Recommendation
User
```

Regra:

```txt
Model representa estrutura de dados.
Service executa regra.
```

---

## 20. Regras das strategies

Use `strategies/` quando existem várias formas de fazer a mesma coisa.

No scraper:

```txt
beautifulsoup_strategy.py
playwright_strategy.py
trafilatura_strategy.py
firecrawl_strategy.py
```

Regra:

```txt
Strategy é algoritmo alternativo.
Service escolhe qual usar.
```

Exemplo:

```txt
URL simples        → BeautifulSoup
Site com JS        → Playwright
Artigo/blog        → trafilatura
Texto limpo/RAG    → Firecrawl
```

O código da rota não deve escolher a strategy.

Errado:

```python
@router.post('/jobs')
async def create_job(payload):
    if payload.use_js:
        PlaywrightStrategy()
```

Certo:

```python
service.create_job(payload)
```

E o service ou selector decide.

---

## 21. Regras dos validators

Validators verificam qualidade e consistência.

Exemplo no scraping:

```txt
URL válida?
Texto vazio?
Página bloqueada?
Conteúdo pequeno demais?
Captcha?
Erro 404?
Muito menu e pouco conteúdo?
```

Regra:

```txt
Validator responde se algo é válido ou inválido.
Service decide o que fazer com isso.
```

---

## 22. Regras dos workers

Workers executam tarefas demoradas.

Eles servem para:

```txt
scraping pesado
geração de embeddings
execução de agentes
processamento de documentos
pipelines longos
```

Eles não devem conter toda a regra de negócio.

Errado:

```txt
workers/scraper_worker/
├── playwright.py
├── validators.py
├── database.py
├── recommendation.py
└── rag.py
```

Certo:

```txt
workers/scraper_worker/
├── run.py
└── tasks.py
```

E o worker chama:

```txt
modules/scraping/services/scraping_service.py
```

Regra:

```txt
Worker executa.
Módulo sabe fazer.
```

---

## 23. Regras da fila

A fila desacopla a API dos trabalhos demorados.

Fluxo correto:

```txt
Frontend
↓
API
↓
cria job no banco
↓
envia job para fila
↓
worker pega job
↓
worker executa
↓
worker atualiza status
↓
frontend consulta status
```

Regra:

```txt
A API não deve travar esperando tarefa longa terminar.
```

No começo, é aceitável executar direto, mas o código deve estar preparado para migrar para fila.

---

## 24. Regras do banco relacional

O banco relacional é a fonte da verdade.

Use PostgreSQL/Supabase para:

```txt
startups
users
documents
sources
scraping_jobs
scraping_results
recommendations
agent_runs
rag_queries
status
histórico
metadados
```

Regra:

```txt
Se é dado estruturado e importante, vai para PostgreSQL.
```

---

## 25. Regras do banco vetorial

Use Qdrant para:

```txt
chunks
embeddings
metadata de busca
vetores semânticos
```

Regra:

```txt
Qdrant serve para busca semântica.
PostgreSQL serve como fonte da verdade.
```

Não salve tudo apenas no Qdrant.

Errado:

```txt
guardar startup inteira só no Qdrant
```

Certo:

```txt
PostgreSQL:
startup, document, chunk_id, metadata

Qdrant:
chunk_id, embedding, payload mínimo
```

---

## 26. Regras dos IDs

Use IDs para conectar PostgreSQL e Qdrant.

Exemplo:

```txt
documents.id       → PostgreSQL
chunks.id          → PostgreSQL
qdrant.payload     → chunk_id, document_id, startup_id
```

Regra:

```txt
Todo vetor no Qdrant precisa apontar para um registro real no PostgreSQL.
```

---

## 27. Regras do RAG

O RAG deve seguir fluxo controlado:

```txt
pergunta
↓
busca lexical
+
busca vetorial
↓
reranking
↓
contexto
↓
geração
↓
resposta com citações
```

Regra:

```txt
LLM não responde de memória quando deveria usar documentos.
```

O RAG deve conseguir mostrar de onde veio a informação.

---

## 28. Regras dos agentes

Agentes não devem virar “deuses” do sistema.

Eles não fazem tudo sozinhos.

Eles usam ferramentas.

Exemplo certo:

```txt
SearchAgent usa ScrapingTool
RagAgent usa RagService
RecommendationAgent usa RecommendationService
ValidationAgent usa Validator
```

Exemplo errado:

```txt
Um agente gigante que scrapeia, limpa, salva no banco, gera embedding, recomenda e responde.
```

Regra:

```txt
Agente orquestra.
Service executa regra.
Tool conecta agente ao service.
```

---

## 29. Regras dos prompts

Prompts devem ficar separados do código.

Estrutura:

```txt
packages/prompts/
├── extraction_prompt.md
├── validation_prompt.md
├── recommendation_prompt.md
└── rag_answer_prompt.md
```

Regra:

```txt
Prompt é parte do sistema e deve ser versionado.
```

Não deixe prompt gigante perdido dentro de função Python.

---

## 30. Regras do `shared/`

`shared/` guarda coisas realmente reutilizáveis.

Pode ter:

```txt
logger
errors
utils
security
constants
types comuns
```

Mas cuidado para não virar lixão.

Regra:

```txt
Se pertence a um módulo específico, fica no módulo.
Se é usado por vários módulos, pode ir para shared.
```

Exemplo:

```txt
limpar_url() → pode ser shared
validar_qualidade_scraping() → fica em scraping/validators
```

---

## 31. Regras do `config/`

Configuração global fica em `config/`.

Exemplo:

```txt
DATABASE_URL
QDRANT_URL
REDIS_URL
OPENAI_API_KEY
COHERE_API_KEY
ENVIRONMENT
```

Regra:

```txt
Nunca espalhe variável de ambiente pelo código inteiro.
```

Crie um `settings.py` central.

---

## 32. Regras do `.env`

Nunca coloque segredo no código.

Errado:

```python
OPENAI_API_KEY = 'sk-...'
```

Certo:

```env
OPENAI_API_KEY=...
```

E no código:

```python
settings.OPENAI_API_KEY
```

Regra:

```txt
Chave secreta só em .env ou secret manager.
```

---

## 33. Regras de nomes

Use nomes claros e consistentes.

Bom:

```txt
scraping_service.py
scraping_repository.py
content_quality_validator.py
playwright_strategy.py
```

Ruim:

```txt
utils2.py
testando.py
novo.py
main2.py
faz_tudo.py
```

Regra:

```txt
O nome do arquivo deve dizer o que ele faz.
```

---

## 34. Regras dos `main.py`

Pode ter mais de um ponto de entrada, mas com clareza.

Recomendado:

```txt
apps/api/src/main.py
workers/scraper_worker/run.py
workers/embedding_worker/run.py
workers/agent_worker/run.py
```

Regra:

```txt
main.py só para API principal.
run.py para workers.
```

O `main.py` não deve ter regra de negócio.

---

## 35. Regras dos imports

Fluxo recomendado:

```txt
routes → services → repositories
routes → schemas
services → validators/strategies/repositories
workers → services
```

Evite:

```txt
repository importando service
service importando route
model importando controller
```

Regra:

```txt
Camada de baixo não deve depender da camada de cima.
```

---

## 36. Regras de dependência entre módulos

Um módulo pode chamar outro, mas com cuidado.

Exemplo aceitável:

```txt
recommendations → rag
agents → rag
agents → scraping
ingestion → scraping_repository para buscar dado bruto
```

Mas evite acoplamento bagunçado.

Regra:

```txt
Módulos conversam por services públicos, não por arquivos internos.
```

Certo:

```python
from modules.rag.services.rag_service import RagService
```

Ruim:

```python
from modules.rag.retriever.private_internal_file import alguma_funcao
```

---

## 37. Regra da evolução

Não crie arquitetura máxima no primeiro dia.

Comece com o necessário:

```txt
apps/api
apps/web
modules/scraping
modules/startups
workers/scraper_worker
database/relational
```

Depois adicione:

```txt
ingestion
embedding_worker
database/vector
rag
agents
recommendations
```

Regra:

```txt
Arquitetura deve crescer com o problema.
```

---

## 38. Regra para não virar monolito bagunçado

Monolito modular não é colocar tudo junto.

É um único backend, mas com fronteiras internas.

Regra:

```txt
Cada módulo deve conseguir ser entendido isoladamente.
```

Se para entender `scraping` você precisa abrir muitos arquivos de `rag`, `agents` e `recommendations`, existe acoplamento demais.

---

## 39. Regra para futura migração para microserviços

Desenhe módulos como se um dia pudessem sair do monolito.

Isso significa:

```txt
cada módulo com service próprio
repository próprio
schemas próprios
rotas próprias
responsabilidade clara
mínimo acoplamento
```

Hoje:

```txt
modules/scraping/
```

Futuro:

```txt
services/scraping-service/
```

Regra:

```txt
Não comece com microserviços, mas programe com fronteiras claras.
```

---

## 40. Primeiro fluxo funcional recomendado

O primeiro objetivo não é construir tudo.

O primeiro objetivo deve ser:

```txt
Frontend com input de URL
↓
POST /scraping/jobs
↓
API cria job
↓
Worker executa scraping
↓
Banco salva resultado
↓
GET /scraping/jobs/{id}
↓
GET /scraping/results/{id}
↓
Frontend mostra texto extraído
```

Regra:

```txt
Construa fluxo vertical antes de construir todas as camadas horizontais.
```

Melhor ter um fluxo completo pequeno funcionando do que 30 pastas vazias.

---

## 41. Regra do tratamento de dados

Scraping não é suficiente.

Depois de coletar, sempre passe por ingestion:

```txt
raw_html/raw_text
↓
cleaning
↓
normalization
↓
extraction
↓
chunking
```

Regra:

```txt
Dado bruto nunca vai direto para RAG.
```

---

## 42. Regra dos status

Toda tarefa longa deve ter status.

Exemplo:

```txt
pending
running
completed
failed
```

Para scraping:

```txt
scraping_jobs.status
```

Para embeddings:

```txt
embedding_jobs.status
```

Para agentes:

```txt
agent_runs.status
```

Regra:

```txt
Frontend acompanha status. Worker atualiza status.
```

---

## 43. Regra de logs

Toda etapa importante precisa logar.

Logue:

```txt
job criado
worker iniciou
estratégia escolhida
scraping falhou
embedding criado
RAG executado
agente terminou
```

Regra:

```txt
Sistema com worker sem log é impossível de debugar.
```

---

## 44. Regra de erros

Não deixe erro explodir sem controle.

Use erros padronizados:

```txt
ScrapingFailedError
InvalidUrlError
EmbeddingGenerationError
RagContextNotFoundError
AgentExecutionError
```

Regra:

```txt
Erro interno vira resposta controlada na API.
```

---

## 45. Regra de testes

Teste por camada.

Prioridade:

```txt
services
validators
strategies
repositories
rotas principais
```

Exemplo:

```txt
test_content_quality_validator.py
test_strategy_selector.py
test_scraping_service.py
```

Regra:

```txt
Service e validator precisam ser fáceis de testar sem subir frontend.
```

---

## 46. Checklist final da arquitetura

Antes de criar qualquer arquivo, pergunte:

```txt
Isso pertence ao frontend, backend, worker ou infra?
Isso é regra de negócio ou acesso a banco?
Isso é tarefa rápida ou demorada?
Esse código será usado por mais de um módulo?
Essa pasta existe por necessidade real ou só por estética?
Esse módulo conseguiria virar serviço separado no futuro?
```

Se responder bem essas perguntas, a arquitetura está sendo respeitada.

---

## 47. Regra mais importante

A regra mais importante é:

```txt
Não duplique lógica.
Não misture responsabilidades.
Não complique antes da hora.
```

Resumo direto:

```txt
Frontend chama API.
API chama service.
Service aplica regra.
Repository acessa banco.
Worker executa tarefa pesada.
PostgreSQL guarda verdade.
Qdrant guarda vetores.
Agente orquestra, não faz tudo.
```

Se essas regras forem seguidas, o projeto começa simples, cresce bem e não vira um monolito bagunçado.
