# Lógica do Backend — NVIDIA Startup AI Radar

## 1. Visão geral

A lógica principal do backend do projeto é construir um fluxo capaz de buscar startups, coletar dados públicos, tratar essas informações, armazenar os dados em bancos adequados, recuperar conhecimento com RAG e gerar recomendações personalizadas de tecnologias NVIDIA.

Em uma visão simples, o sistema funciona assim:

```txt
Entrada do usuário
↓
Busca e planejamento
↓
Scraping
↓
Tratamento dos dados
↓
Ingestão nos bancos
↓
Busca lexical + busca semântica
↓
Reranking
↓
RAG
↓
Recomendação
↓
Briefing final
```

O objetivo não é apenas responder perguntas com IA. O objetivo é criar um pipeline completo de inteligência capaz de transformar dados públicos desorganizados em diagnóstico técnico e recomendação estratégica.

---

## 2. Lógica central do sistema

A lógica do backend pode ser resumida em uma frase:

> O sistema coleta informações públicas sobre startups, trata e estrutura esses dados, salva tudo em bancos de dados, usa busca híbrida e RAG para recuperar evidências, aplica reranking para selecionar os melhores trechos e gera recomendações NVIDIA com justificativa técnica e de negócio.

Fluxo principal:

```txt
Usuário faz uma consulta
↓
Sistema entende o que deve buscar
↓
Scraper coleta dados públicos
↓
Ingestion limpa e organiza os dados
↓
Dados estruturados vão para PostgreSQL/Supabase
↓
Chunks e embeddings vão para Qdrant
↓
RAG recupera informações relevantes
↓
Reranker ordena as melhores evidências
↓
Motor de recomendação cruza perfil da startup com tecnologias NVIDIA
↓
Sistema gera briefing final
```

---

## 3. Etapa 1 — Entrada do usuário

A entrada pode ser uma consulta como:

```txt
Quero analisar startups brasileiras de IA na área de saúde.
```

Ou uma URL específica:

```txt
https://startup.com.br
```

Ou o nome de uma empresa:

```txt
Analise a startup X.
```

Essa entrada chega pela API do backend.

Exemplo de endpoint:

```txt
POST /analysis/jobs
POST /scraping/jobs
GET /analysis/jobs/{id}
GET /analysis/results/{id}
```

A API não deve fazer todo o processamento diretamente. Ela deve apenas receber a requisição, validar os dados e criar um job para o worker executar.

---

## 4. Etapa 2 — Search Planner

Antes de sair fazendo scraping, o sistema precisa decidir o que buscar.

O Search Planner é responsável por transformar a consulta do usuário em uma estratégia de busca.

Exemplo:

Entrada:

```txt
Startups brasileiras de IA para atendimento ao cliente
```

O Search Planner pode gerar buscas como:

```txt
startups brasileiras IA atendimento ao cliente
startups brasileiras chatbot IA B2B
startup brasileira automação atendimento inteligência artificial
empresa brasileira customer support AI
```

Responsabilidades do Search Planner:

```txt
entender a intenção do usuário
criar termos de busca
priorizar fontes
selecionar possíveis URLs
organizar o plano de coleta
```

Essa etapa pode ser feita com regras simples no começo e depois evoluir para um agente com LangGraph.

---

## 5. Etapa 3 — Scraping

O scraping é a etapa que coleta dados públicos sobre startups e tecnologias.

Fontes possíveis:

```txt
sites oficiais das startups
blogs das startups
páginas de carreira
notícias
diretórios públicos de startups
páginas de aceleradoras
materiais oficiais da NVIDIA
```

O scraper deve coletar dados como:

```txt
nome da startup
site
descrição do produto
setor de atuação
tecnologias usadas
clientes citados
funding
fundadores
notícias relevantes
evidências de uso de IA
```

Tecnologias possíveis:

```txt
BeautifulSoup → páginas HTML simples
Playwright → páginas dinâmicas com JavaScript
Scrapy → crawling em maior escala
trafilatura → extração de texto principal
Firecrawl → extração limpa para RAG
```

A regra é:

```txt
Scraping coleta.
Ingestion trata.
RAG recupera.
Recommendation recomenda.
```

O scraper não deve gerar recomendação e nem fazer RAG diretamente.

---

## 6. Etapa 4 — Validação do conteúdo coletado

Depois do scraping, o sistema precisa verificar se o conteúdo coletado tem qualidade antes de salvar no banco, gerar embeddings ou usar esse material no RAG.

Essa etapa existe para impedir que dados ruins, incompletos, duplicados, genéricos ou sem evidência entrem no sistema e prejudiquem as próximas etapas da pipeline.

A validação deve acontecer em três níveis:

```txt
1. Validação técnica
   → verifica se a coleta funcionou corretamente

2. Validação textual
   → verifica se o texto extraído tem qualidade mínima

3. Validação semântica/evidencial
   → verifica se o conteúdo realmente serve como evidência para análise da startup
```

---

### 6.1 Validação técnica

A validação técnica verifica se a página foi acessada corretamente e se o scraper conseguiu coletar algum conteúdo válido.

Exemplos de perguntas dessa etapa:

```txt
A página retornou erro 404?
A página retornou erro 403?
A requisição deu timeout?
A página retornou erro 500?
O conteúdo veio vazio?
A página tem captcha?
A página retornou bloqueio de acesso?
A página exigiu login?
Existe URL de origem?
O HTML veio quebrado?
A URL final é diferente da URL esperada?
```

Parâmetros recomendados:

```txt
status_code
blocked_or_captcha
request_error
timeout
source_url_present
final_url
html_length
content_type
```

Esses parâmetros devem ser avaliados por código, sem necessidade de IA, porque são objetivos.

Exemplo:

```txt
status_code >= 400
→ conteúdo inválido

captcha detectado
→ conteúdo bloqueado

source_url ausente
→ conteúdo sem rastreabilidade

html_length muito pequeno
→ possível erro de coleta
```

---

### 6.2 Validação textual

Depois de verificar que a coleta funcionou tecnicamente, o sistema precisa analisar se o texto extraído tem qualidade.

Nem todo texto coletado é útil. Às vezes o scraper captura apenas menu, rodapé, botão, banner de cookie ou texto repetido.

Exemplos de perguntas dessa etapa:

```txt
O texto está vazio?
O conteúdo tem poucos caracteres?
O conteúdo tem poucas palavras?
O texto é só menu e rodapé?
O texto tem muita repetição?
O texto tem excesso de links?
O conteúdo parece boilerplate?
O idioma é compatível com o projeto?
O conteúdo está duplicado?
```

Parâmetros recomendados:

```txt
clean_text_length
word_count
text_density
boilerplate_ratio
duplicate_ratio
link_ratio
language
```

Exemplos de regras iniciais:

```txt
clean_text_length < 300
→ conteúdo ruim

clean_text_length entre 300 e 800
→ conteúdo fraco

clean_text_length acima de 800
→ conteúdo aceitável

word_count < 80
→ pouco conteúdo útil

duplicate_ratio alto
→ conteúdo repetitivo

boilerplate_ratio alto
→ muito menu, rodapé ou navegação
```

Essa etapa também deve ser feita principalmente por código, pois mede características objetivas do texto.

---

### 6.3 Validação semântica/evidencial

A validação semântica verifica se o conteúdo realmente é útil para o objetivo do projeto.

No contexto do NVIDIA Startup AI Radar, não basta a página abrir e ter texto. O conteúdo precisa ajudar a entender a startup, seu produto, seu uso de IA, sua maturidade técnica e possíveis recomendações NVIDIA.

Exemplos de perguntas dessa etapa:

```txt
O texto fala da startup correta?
O nome da startup aparece no conteúdo?
O texto descreve o produto ou serviço da empresa?
O texto menciona inteligência artificial?
A menção à IA é concreta ou genérica?
Existe evidência real de uso de IA?
A fonte é confiável?
A fonte é oficial, notícia, diretório ou agregador?
A informação tem URL rastreável?
O conteúdo é suficiente para classificar a startup?
O conteúdo pode apoiar uma recomendação NVIDIA?
```

Parâmetros recomendados:

```txt
startup_name_match
source_type
source_reliability
ai_keyword_score
product_description_present
evidence_strength
source_url_present
published_date
needs_llm_review
```

A força da evidência pode ser classificada assim:

```txt
none
→ não há evidência relevante

weak
→ menciona IA de forma genérica ou superficial

medium
→ descreve uma aplicação de IA no produto ou operação

strong
→ descreve aplicação, tecnologia, cliente, métrica, caso real ou detalhe técnico
```

Exemplo:

```txt
"A empresa usa inteligência artificial para transformar negócios."
→ evidência fraca

"A startup utiliza modelos de linguagem para automatizar atendimento em centrais de suporte."
→ evidência média

"A startup usa modelos de visão computacional para detectar defeitos industriais em tempo real para clientes do setor automotivo."
→ evidência forte
```

---

### 6.4 Quando usar agente/LLM na validação

O agente/LLM não deve ser o validador principal.

A primeira linha de validação deve ser feita por regras determinísticas, porque são mais rápidas, baratas e previsíveis.

O agente deve entrar apenas como fallback em casos ambíguos.

A regra geral é:

```txt
Código valida qualidade técnica.
Código valida qualidade textual.
Agente valida incerteza semântica.
Service decide o que fazer.
```

Um conteúdo é considerado ambíguo quando passa nas validações técnicas e textuais mínimas, mas ainda não há segurança suficiente sobre sua relevância semântica, força de evidência ou relação direta com a startup analisada.

Exemplos de conteúdo ambíguo:

```txt
Menciona IA, mas de forma muito genérica.
Fala da empresa, mas não deixa claro se ela usa IA.
Fala de automação, mas não se sabe se é IA ou regra tradicional.
O nome da startup aparece, mas pode ser outra empresa com nome parecido.
A fonte é um diretório e a evidência é superficial.
O texto é grande, mas não traz evidência concreta.
A página parece relevante, mas não deixa claro se fala do produto certo.
```

Critérios práticos para chamar IA:

```txt
technical_score >= 0.70
text_score >= 0.50
evidence_score entre 0.30 e 0.70
```

Ou seja:

```txt
Muito ruim
→ não manda para IA, tenta fallback de scraping

Muito bom
→ aceita direto

Meio termo/incerto
→ manda para IA analisar
```

Exemplo de decisão:

```txt
Texto tecnicamente válido
↓
Texto com tamanho aceitável
↓
Menciona IA, mas de forma genérica
↓
Sistema não sabe se é evidência real ou marketing
↓
Chama agente de validação semântica
```

O agente pode avaliar:

```txt
O texto fala da startup correta?
A evidência de IA é concreta?
A fonte parece confiável?
O conteúdo pode ser usado no RAG?
O sistema deve aceitar, rejeitar ou buscar outra fonte?
```

---

### 6.5 Estratégia de fallback

Se o conteúdo for ruim, o sistema pode tentar outra estratégia de scraping.

Exemplo:

```txt
BeautifulSoup falhou
↓
Tenta Playwright
↓
Se ainda falhar, tenta Firecrawl
↓
Se continuar ruim, marca como failed
```

O fallback deve ser acionado principalmente quando houver problema técnico ou textual.

Exemplos:

```txt
Página com pouco texto útil
→ tentar outra estratégia

Página dependente de JavaScript
→ tentar Playwright

Texto cheio de menu e rodapé
→ tentar trafilatura ou Firecrawl

Página bloqueada
→ marcar como blocked ou tentar estratégia permitida

Conteúdo sem evidência, mas fonte parece importante
→ buscar novas fontes

Conteúdo ambíguo
→ chamar agente/LLM
```

---

### 6.6 Score de qualidade

Para facilitar a decisão automática, cada conteúdo coletado pode receber uma nota final de qualidade.

Uma fórmula inicial pode ser:

```txt
quality_score =
    technical_score * 0.30
    + text_score * 0.30
    + evidence_score * 0.40
```

Pesos recomendados:

```txt
Qualidade técnica: 30%
Qualidade textual: 30%
Qualidade semântica/evidencial: 40%
```

A parte semântica recebe maior peso porque o objetivo do projeto não é apenas coletar texto, mas coletar evidências úteis para análise de startups e recomendação de tecnologias NVIDIA.

Critérios iniciais de decisão:

```txt
quality_score >= 0.75
→ aceita o conteúdo

0.45 <= quality_score < 0.75
→ conteúdo intermediário; pode chamar agente ou buscar mais fontes

quality_score < 0.45
→ rejeita ou tenta fallback de scraping
```

---

### 6.7 Exemplo de saída da validação

Exemplo de conteúdo aceito:

```json
{
  "url": "https://startup.com.br/sobre",
  "status": "accepted",
  "technical_score": 0.95,
  "text_score": 0.82,
  "evidence_score": 0.76,
  "quality_score": 0.83,
  "source_type": "official_site",
  "source_reliability": "high",
  "evidence_strength": "medium",
  "needs_llm_review": false,
  "fallback_required": false,
  "reason": "Página acessível, texto suficiente, fonte oficial e conteúdo relacionado ao produto da startup."
}
```

Exemplo de conteúdo que precisa de fallback:

```json
{
  "url": "https://startup.com.br",
  "status": "needs_fallback",
  "technical_score": 0.85,
  "text_score": 0.22,
  "evidence_score": 0.10,
  "quality_score": 0.34,
  "source_type": "official_site",
  "source_reliability": "high",
  "evidence_strength": "weak",
  "needs_llm_review": false,
  "fallback_required": true,
  "reason": "A página respondeu, mas o texto extraído contém principalmente menu, rodapé e poucos dados úteis."
}
```

Exemplo de conteúdo ambíguo que precisa de IA:

```json
{
  "url": "https://noticia.com.br/startup-x-ia",
  "status": "needs_llm_review",
  "technical_score": 0.90,
  "text_score": 0.78,
  "evidence_score": 0.45,
  "quality_score": 0.68,
  "source_type": "news",
  "source_reliability": "medium",
  "evidence_strength": "weak",
  "needs_llm_review": true,
  "fallback_required": false,
  "reason": "Texto possui conteúdo suficiente e menciona IA, mas não está claro se a startup realmente usa IA no produto ou apenas em discurso comercial."
}
```

---

### 6.8 Regra principal dessa etapa

A regra mais importante é:

```txt
Não basta a página abrir.
Não basta ter texto.
O texto precisa ser útil, rastreável e relevante para a análise da startup.
```

Resumo da decisão:

```txt
Erro técnico
→ fallback ou failed

Texto ruim
→ fallback ou rejected

Texto bom e evidência forte
→ accepted

Texto bom, mas evidência ambígua
→ needs_llm_review

Texto sem rastreabilidade
→ não deve virar evidência forte
```

Essa lógica evita que dados ruins entrem no banco, melhora a qualidade dos embeddings, reduz ruído no RAG, fortalece o reranking e aumenta a confiabilidade das recomendações finais.

---

## 7. Etapa 5 — Ingestion e tratamento dos dados

Ingestion é a etapa que transforma dado bruto em dado utilizável.

O fluxo é:

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
↓
embedding
```

### 7.1 Cleaning

Remove sujeira do texto:

```txt
menus
rodapés
scripts
CSS
HTML desnecessário
textos repetidos
espaços excessivos
```

### 7.2 Normalization

Padroniza os dados:

```txt
nomes
URLs
datas
setores
categorias
idioma
formato dos campos
```

### 7.3 Extraction

Extrai campos importantes:

```txt
nome da empresa
produto
setor
tecnologias
fundadores
clientes
sinais de IA
problemas técnicos
fontes usadas
```

### 7.4 Chunking

Divide documentos longos em pedaços menores.

Exemplo:

```txt
Documento completo
↓
Chunk 1
Chunk 2
Chunk 3
Chunk 4
```

Cada chunk precisa manter metadados:

```txt
chunk_id
document_id
startup_id
source_url
título da fonte
data de coleta
```

---

## 8. Etapa 6 — Banco relacional

O banco relacional é a fonte da verdade do sistema.

Tecnologia recomendada:

```txt
PostgreSQL ou Supabase
```

Ele guarda dados estruturados, como:

```txt
startups
sources
documents
chunks
scraping_jobs
analysis_jobs
recommendations
agent_runs
rag_queries
users
status
histórico
```

Regra principal:

```txt
Se é dado estruturado e importante, vai para PostgreSQL/Supabase.
```

Exemplo:

```txt
startups
- id
- name
- website
- sector
- description
- ai_maturity
- created_at

sources
- id
- startup_id
- url
- source_type
- collected_at

scraping_jobs
- id
- status
- target_url
- error_message
- created_at
```

---

## 9. Etapa 7 — Banco vetorial

O banco vetorial é usado para busca semântica.

Tecnologia recomendada:

```txt
Qdrant
```

Ele guarda:

```txt
embeddings
chunks vetorizados
metadados mínimos para busca
```

Regra principal:

```txt
Qdrant não substitui PostgreSQL.
Qdrant serve para busca semântica.
PostgreSQL serve como fonte da verdade.
```

Exemplo:

```txt
PostgreSQL:
chunk_id, document_id, startup_id, text, source_url

Qdrant:
vector, chunk_id, document_id, startup_id, source_url
```

Todo vetor no Qdrant precisa apontar para um registro real no PostgreSQL.

---

## 10. Etapa 8 — Busca lexical

Busca lexical é busca por palavras exatas ou termos próximos.

Ela é útil para encontrar:

```txt
nomes de empresas
nomes de tecnologias
siglas
termos técnicos
nomes de produtos
palavras específicas
```

Exemplo:

Se o usuário pergunta sobre:

```txt
TensorRT-LLM
```

A busca lexical ajuda a encontrar documentos que mencionam exatamente esse termo.

Tecnologia possível:

```txt
BM25
PostgreSQL full-text search
Elasticsearch
OpenSearch
```

No início, PostgreSQL full-text search pode ser suficiente.

---

## 11. Etapa 9 — Busca semântica

Busca semântica encontra trechos pelo significado, mesmo quando as palavras não são exatamente iguais.

Exemplo:

Pergunta:

```txt
Como reduzir latência em modelos generativos?
```

A busca semântica pode encontrar trechos sobre:

```txt
inference optimization
serving de modelos
TensorRT-LLM
Triton Inference Server
batching
quantização
```

Mesmo que o texto não use exatamente a palavra “latência”.

Tecnologia:

```txt
Embeddings + Qdrant
```

---

## 12. Etapa 10 — Busca híbrida

A busca híbrida combina:

```txt
busca lexical
+
busca semântica
```

Por que usar as duas?

Porque cada uma resolve um problema diferente.

```txt
Busca lexical:
boa para termos exatos.

Busca semântica:
boa para significado e contexto.
```

Exemplo:

```txt
Pergunta: Qual tecnologia NVIDIA ajuda no serving de modelos em produção?
```

A busca lexical pode encontrar:

```txt
Triton Inference Server
NVIDIA NIM
TensorRT-LLM
```

A busca semântica pode encontrar trechos sobre:

```txt
deploy
inferência
produção
otimização
model serving
```

Depois, os resultados são unidos e enviados para o reranker.

---

## 13. Etapa 11 — Reranking

O reranking reordena os trechos encontrados pela busca híbrida.

A busca inicial pode retornar muitos chunks. Nem todos são igualmente bons.

O reranker decide quais trechos são mais relevantes para a pergunta.

Fluxo:

```txt
Pergunta do usuário
↓
Busca lexical retorna 20 trechos
↓
Busca semântica retorna 20 trechos
↓
Sistema junta os resultados
↓
Reranker reordena
↓
Seleciona os melhores 5 ou 10 chunks
```

Tecnologia possível:

```txt
Cohere Rerank
Cross-encoder
modelo reranker open-source
```

Regra:

```txt
Retriever busca candidatos.
Reranker escolhe os melhores.
```

---

## 14. Etapa 12 — RAG

RAG significa Retrieval-Augmented Generation.

Ou seja:

```txt
A IA não responde só com memória própria.
Ela primeiro recupera documentos relevantes.
Depois responde usando esses documentos como contexto.
```

Fluxo do RAG:

```txt
Pergunta
↓
Busca híbrida
↓
Reranking
↓
Contexto selecionado
↓
LLM
↓
Resposta com citações
```

O RAG deve ser usado para:

```txt
responder perguntas sobre tecnologias NVIDIA
explicar por que uma tecnologia foi recomendada
comparar alternativas
fundamentar diagnóstico técnico
trazer evidências das fontes coletadas
```

Regra importante:

```txt
Se a resposta depende dos documentos, o LLM não deve responder de memória.
```

---

## 15. Etapa 13 — Classificação da startup

Depois de coletar e tratar dados, o sistema deve classificar a startup.

Categorias possíveis:

```txt
AI-native
AI-enabled
Non-AI
```

### AI-native

A startup tem IA no centro do produto ou operação.

Exemplo:

```txt
produto depende diretamente de modelos de IA
usa agentes para executar workflows
cria automação inteligente de ponta a ponta
usa dados proprietários para melhorar o sistema
```

### AI-enabled

A startup usa IA como funcionalidade auxiliar.

Exemplo:

```txt
usa chatbot simples
usa IA para resumo
usa IA em uma parte pequena do produto
```

### Non-AI

Não há evidência forte de uso de IA.

Exemplo:

```txt
site não menciona IA
produto parece tradicional
não há sinais técnicos suficientes
```

Essa classificação ajuda o motor de recomendação.

---

## 16. Etapa 14 — Validação de evidências

O sistema precisa evitar recomendações sem base.

Por isso, cada afirmação importante deve ter evidência.

Exemplo:

Afirmação:

```txt
A startup usa IA generativa para atendimento ao cliente.
```

Evidência esperada:

```txt
URL da fonte
trecho extraído
data de coleta
confiabilidade da fonte
```

O Evidence Validator verifica se a recomendação está apoiada por fontes suficientes.

Regra:

```txt
Sem evidência, a afirmação deve ser marcada como incerta.
```

---

## 17. Etapa 15 — Motor de recomendação

O motor de recomendação cruza o perfil da startup com as tecnologias NVIDIA.

Entrada do motor:

```txt
perfil da startup
setor de atuação
tecnologias usadas
gaps técnicos
maturidade AI-native
evidências coletadas
contexto recuperado pelo RAG
```

Saída do motor:

```txt
tecnologias NVIDIA recomendadas
justificativa técnica
justificativa de negócio
prioridade
complexidade de implementação
próxima ação sugerida
evidências usadas
```

Exemplos de regra:

```txt
Se a startup usa LLMs em atendimento ao cliente:
recomendar NIM, NeMo Guardrails, Triton e TensorRT-LLM.

Se a startup processa muitos dados tabulares:
recomendar RAPIDS, cuDF e cuML.

Se a startup trabalha com voz:
recomendar NVIDIA Riva.

Se a startup atua em saúde:
considerar Clara, MONAI, NIM e AI Enterprise.

Se a startup faz robótica ou simulação:
recomendar Isaac e Omniverse.
```

---

## 18. Etapa 16 — Briefing final

O briefing final é a saída executiva do sistema.

Ele deve conter:

```txt
resumo da startup
setor de atuação
nível de maturidade AI-native
evidências encontradas
principais dores técnicas
tecnologias NVIDIA recomendadas
prioridade de abordagem
justificativa técnica
justificativa de negócio
próxima ação sugerida
fontes usadas
```

Exemplo de estrutura:

```txt
# Briefing — Startup X

## Resumo
A Startup X atua no setor de atendimento ao cliente usando IA generativa para automatizar conversas B2B.

## Diagnóstico
A empresa apresenta sinais de ser AI-native, pois seu produto depende diretamente de automação inteligente baseada em IA.

## Gaps técnicos possíveis
- Dependência de APIs externas
- Risco de latência em escala
- Necessidade de guardrails
- Necessidade de avaliação de respostas

## Recomendações NVIDIA
1. NVIDIA NIM
2. NeMo Guardrails
3. Triton Inference Server
4. TensorRT-LLM

## Justificativa
As tecnologias recomendadas ajudam a reduzir latência, melhorar governança e preparar o sistema para produção.

## Próxima ação
Convidar a startup para uma conversa técnica sobre NVIDIA Inception e otimização de inferência.
```

---

## 19. Papel dos agentes

Os agentes não devem fazer tudo sozinhos.

A regra é:

```txt
Agente orquestra.
Service executa.
Repository salva.
Worker processa.
```

Agentes possíveis:

```txt
Search Planner Agent
Scraper Agent
Extractor Agent
Startup Classifier Agent
Evidence Validator Agent
NVIDIA RAG Agent
Recommendation Agent
Briefing Agent
```

O LangGraph entra para organizar esse fluxo.

Exemplo:

```txt
Search Planner Agent
↓
Scraper Agent
↓
Extractor Agent
↓
Classifier Agent
↓
Evidence Validator Agent
↓
RAG Agent
↓
Recommendation Agent
↓
Briefing Agent
```

Cada agente deve usar tools/services, e não conter toda a lógica dentro dele.

Errado:

```txt
Um agente gigante que scrapeia, limpa, salva, busca, ranqueia, recomenda e gera briefing.
```

Certo:

```txt
Agentes pequenos coordenando services especializados.
```

---

## 20. Papel dos workers

Workers executam tarefas demoradas fora da API principal.

Exemplos:

```txt
scraping pesado
geração de embeddings
execução de agentes
processamento de documentos
criação de briefing
```

Fluxo correto:

```txt
Frontend
↓
API
↓
Cria job no banco
↓
Envia para fila
↓
Worker executa
↓
Worker atualiza status
↓
Frontend consulta resultado
```

Por que usar worker?

Porque scraping, embeddings e agentes podem demorar.

A API não deve ficar travada esperando tudo terminar.

---

## 21. Status dos jobs

Toda tarefa longa deve ter status.

Exemplo:

```txt
pending
running
completed
failed
```

Exemplo de fluxo:

```txt
Usuário cria análise
↓
status = pending
↓
worker começa
↓
status = running
↓
worker termina
↓
status = completed
```

Se der erro:

```txt
status = failed
error_message = motivo do erro
```

Isso permite que o frontend mostre o andamento para o usuário.

---

## 22. Organização dos módulos

Estrutura lógica recomendada:

```txt
modules/
├── scraping/
├── ingestion/
├── startups/
├── rag/
├── agents/
└── recommendations/
```

Responsabilidade de cada módulo:

```txt
scraping
→ coleta dados públicos

ingestion
→ limpa, normaliza, extrai campos e cria chunks

startups
→ organiza dados principais das empresas

rag
→ faz busca lexical, semântica, reranking e geração com contexto

agents
→ orquestra o fluxo multiagente com LangGraph

recommendations
→ gera recomendações NVIDIA
```

---

## 23. Fluxo vertical mínimo para começar

Não tente fazer tudo de uma vez.

O primeiro fluxo funcional deve ser pequeno:

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

Depois você evolui:

```txt
1. Scraping funcionando
2. Ingestion funcionando
3. Banco relacional funcionando
4. Chunking funcionando
5. Embeddings funcionando
6. Qdrant funcionando
7. Busca lexical funcionando
8. Busca semântica funcionando
9. Reranking funcionando
10. RAG funcionando
11. Recomendação funcionando
12. LangGraph orquestrando tudo
13. Briefing final
```

---

## 24. Ordem recomendada de desenvolvimento

### Fase 1 — Scraping básico

Objetivo:

```txt
Receber uma URL e extrair texto útil.
```

Entregáveis:

```txt
endpoint para criar job de scraping
worker simples
scraper com BeautifulSoup/trafilatura
salvar resultado bruto
consultar status
consultar resultado
```

---

### Fase 2 — Tratamento e banco relacional

Objetivo:

```txt
Limpar e estruturar os dados coletados.
```

Entregáveis:

```txt
módulo ingestion
normalização de texto
extração de campos principais
tabelas no PostgreSQL/Supabase
repositories
```

---

### Fase 3 — Chunking e embeddings

Objetivo:

```txt
Preparar os documentos para busca semântica.
```

Entregáveis:

```txt
chunks dos documentos
geração de embeddings
salvar vetores no Qdrant
ligação entre PostgreSQL e Qdrant por IDs
```

---

### Fase 4 — Busca híbrida

Objetivo:

```txt
Combinar busca lexical e semântica.
```

Entregáveis:

```txt
busca lexical com BM25 ou PostgreSQL full-text search
busca semântica com Qdrant
combinação dos resultados
```

---

### Fase 5 — Reranking

Objetivo:

```txt
Selecionar os melhores trechos recuperados.
```

Entregáveis:

```txt
integração com reranker
ordenação dos chunks
seleção do contexto final
```

---

### Fase 6 — RAG

Objetivo:

```txt
Gerar respostas com base em documentos e citações.
```

Entregáveis:

```txt
montagem de contexto
prompt de resposta
resposta com fontes
guardar consultas RAG
```

---

### Fase 7 — Recomendação NVIDIA

Objetivo:

```txt
Recomendar tecnologias NVIDIA com base no perfil da startup.
```

Entregáveis:

```txt
rules engine
scoring
justificativa técnica
justificativa de negócio
prioridade
complexidade
próxima ação
```

---

### Fase 8 — LangGraph e multiagentes

Objetivo:

```txt
Orquestrar o fluxo completo com agentes especializados.
```

Entregáveis:

```txt
Search Planner Agent
Scraper Agent
Extractor Agent
Classifier Agent
Evidence Validator Agent
RAG Agent
Recommendation Agent
Briefing Agent
```

---

### Fase 9 — Briefing final

Objetivo:

```txt
Gerar uma saída clara para o usuário final.
```

Entregáveis:

```txt
relatório executivo
fontes usadas
diagnóstico da startup
recomendações NVIDIA
próxima ação sugerida
```

---

## 25. Resumo da lógica em uma frase

A lógica do backend é:

```txt
Coletar dados públicos → tratar dados → salvar em bancos → recuperar evidências → ranquear contexto → gerar diagnóstico → recomendar tecnologias NVIDIA → produzir briefing final.
```

Ou, de forma mais técnica:

```txt
Scraping → Ingestion → PostgreSQL/Qdrant → Hybrid Search → Reranking → RAG → Recommendation Engine → Briefing.
```

---

## 26. Regra mais importante

A regra mais importante do projeto é separar responsabilidades.

```txt
API coordena.
Worker executa tarefa pesada.
Service aplica regra de negócio.
Repository acessa banco.
Scraper coleta.
Ingestion trata.
RAG recupera contexto.
Reranker ordena evidências.
Recommendation recomenda.
Briefing comunica o resultado.
```

Se essa lógica for respeitada, o projeto começa simples, evolui bem e não vira um monolito bagunçado.
