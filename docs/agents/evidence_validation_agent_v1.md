# Evidence Validation Agent V1 - Plano Arquitetural

## 1. Objetivo

O primeiro agente do sistema sera responsavel por investigar casos em que a
validacao semantica simples do scraper nao conseguiu decidir com seguranca.

Entrada tipica:

```txt
Gemini analisou uma pagina
-> confianca abaixo de 0.80
ou
-> contradicao detectada
ou
-> decision = needs_agent_review
```

O agente devera:

```txt
entender o motivo da incerteza
planejar evidencias adicionais
consultar fontes permitidas
comparar afirmacoes
detectar contradicoes
produzir decisao rastreavel
```

---

## 2. Limite de responsabilidade

O agente decide e coordena.

Ele nao executa scraping diretamente.

```txt
Evidence Validation Agent
-> chama contrato publico do scraping
-> nao importa BeautifulSoup, Playwright ou Trafilatura
```

Ele nao implementa RAG diretamente.

```txt
Evidence Validation Agent
-> chama contrato publico do modulo rag quando existir
```

---

## 3. Entrada publica

DTO conceitual:

```python
@dataclass(frozen=True)
class EvidenceInvestigationInput:
    original_url: str
    title: str | None
    raw_text: str
    quality_score: float
    semantic_confidence: float
    semantic_decision: str
    semantic_reason: str
    contradiction_detected: bool
```

No futuro, a entrada pode incluir:

```txt
startup_id
nome esperado da startup
dominio oficial conhecido
afirmacoes que precisam ser validadas
fontes ja consultadas
```

---

## 4. Saida publica

Decisoes:

```txt
accepted
rejected
needs_more_sources
```

DTO conceitual:

```python
@dataclass(frozen=True)
class EvidenceInvestigationResult:
    decision: str
    reason: str
    sources_consulted: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    contradictions: tuple[str, ...]
```

O scraper deve conhecer somente esse contrato publico.

---

## 5. Estado do grafo

Estado inicial sugerido:

```python
class EvidenceValidationState(TypedDict):
    run_id: str
    original_url: str
    title: str | None
    raw_text: str
    semantic_confidence: float
    semantic_reason: str
    contradiction_detected: bool
    search_queries: list[str]
    requested_urls: list[str]
    evidence_items: list[dict]
    contradictions: list[str]
    iteration: int
    final_decision: str | None
    final_reason: str | None
```

Campos devem ser serializaveis para permitir checkpoint.

---

## 6. Grafo inicial

```txt
START
-> analyze_uncertainty
-> route_after_analysis

route_after_analysis:
    evidencia suficiente
    -> decide_validation

    faltam fontes e existe budget
    -> plan_evidence_search

    contradicao critica
    -> request_human_review

plan_evidence_search
-> request_additional_scraping
-> collect_scraping_results
-> compare_evidence
-> route_after_comparison

route_after_comparison:
    decisao segura
    -> decide_validation

    ainda incerto e existe budget
    -> plan_evidence_search

    limite atingido
    -> finish_needs_more_sources

decide_validation
-> END
```

---

## 7. Nodes planejados

### analyze_uncertainty

```txt
identifica por que Gemini ficou incerto
separa afirmacoes que precisam de evidencia
```

### plan_evidence_search

```txt
gera consultas pequenas e fontes prioritarias
respeita URLs e fontes ja consultadas
```

### request_additional_scraping

```txt
chama contrato publico do modulo scraping
cria jobs para URLs permitidas
```

### collect_scraping_results

```txt
consulta resultados concluidos
transforma em evidencias pequenas e rastreaveis
```

### compare_evidence

```txt
compara afirmacoes entre fontes
registra suporte e contradicoes
```

### decide_validation

```txt
produz accepted ou rejected com justificativa e fontes
```

### finish_needs_more_sources

```txt
encerra quando o budget acaba sem decisao segura
```

### request_human_review

```txt
interrompe o grafo quando a decisao exige pessoa
```

---

## 8. Routers

Routers iniciais:

```txt
route_after_analysis
route_after_comparison
```

Eles devem considerar:

```txt
quantidade de evidencias
qualidade das fontes
contradicoes
semantic_confidence
numero de iteracoes
tool calls restantes
budget restante
```

As condicoes finais pertencem a politicas testaveis, nao apenas ao prompt.

---

## 9. Tools necessarias

Primeira versao:

```txt
request_scraping
get_scraping_job
read_scraping_result
```

Futuras:

```txt
search_web
read_startup_profile
search_existing_documents
search_rag
request_human_review
```

Todas as tools chamam contratos publicos.

---

## 10. Uso de Gemini com LangChain

Gemini sera acessado por um adaptador configurado na factory.

LangChain sera usado para:

```txt
ChatGoogleGenerativeAI
structured output dos nodes semanticos
tool calling quando realmente necessario
mensagens e prompts versionados
```

Nodes que provavelmente usam LLM:

```txt
analyze_uncertainty
plan_evidence_search
compare_evidence
decide_validation
```

Nodes tecnicos nao precisam de LLM:

```txt
request_additional_scraping
collect_scraping_results
controle de limites
routers deterministas
```

---

## 11. Limites iniciais

```txt
max_iterations = 3
max_sources = 5
max_scraping_jobs = 5
max_tool_calls = 12
timeout_total = 5 minutos
```

Os valores devem ser calibrados com testes reais.

Quando o limite for atingido:

```txt
decision = needs_more_sources
motivo explicito
checkpoint preservado
```

---

## 12. Human-in-the-loop

Interromper para revisao humana quando:

```txt
duas fontes fortes se contradizem
identidade da startup permanece incerta
agente quer ampliar muito a busca
decisao possui impacto comercial relevante
```

O estado deve explicar:

```txt
por que interrompeu
quais fontes foram consultadas
qual decisao o agente sugere
qual informacao ainda falta
```

---

## 13. Testes planejados

### Nodes

```txt
analise identifica incerteza
planejamento nao repete fontes
comparacao registra contradicao
decisao inclui fontes
```

### Routers

```txt
evidencia suficiente encerra
falta de evidencia busca nova fonte
contradicao pede humano
limite gera needs_more_sources
```

### Grafo

```txt
aceita apos uma fonte adicional
rejeita apos evidencia contraria
pede mais fontes apos limite
interrompe e retoma revisao humana
```

### Integracao

```txt
tool cria job real de scraping
resultado real volta ao grafo
checkpoint PostgreSQL permite retomada
worker executa o run
```

---

## 14. Fases de implementacao

### Fase 1 - Esqueleto

```txt
instalar LangGraph e LangChain
criar estado tipado
criar grafo minimo com nodes falsos
testar transicoes
```

### Fase 2 - Gemini

```txt
criar adaptador LangChain para Gemini
structured output
prompts versionados
```

### Fase 3 - Scraping tools

```txt
expor contratos publicos do scraping
adaptar contratos como tools
integrar resultados
```

### Fase 4 - Durabilidade

```txt
AgentRun
checkpoint PostgreSQL
agent_worker
fila
```

### Fase 5 - Human review

```txt
interrupt
endpoint de aprovacao
retomada do grafo
```

---

## 15. Criterio de conclusao da V1

O Evidence Validation Agent V1 estara concluido quando:

```txt
receber caso incerto do scraper
executar grafo LangGraph real
usar Gemini por LangChain em nodes semanticos
chamar scraping somente por tools publicas
comparar ao menos duas evidencias
respeitar limites
produzir decisao rastreavel
persistir checkpoint
executar pelo agent_worker
possuir testes unitarios e integrados
```

---

## 16. Proximo passo

Depois desta documentacao, o primeiro passo de codigo sera:

```txt
criar a estrutura minima de modules/agents
instalar LangGraph e LangChain
criar EvidenceValidationState
criar grafo minimo com nodes deterministas falsos
```

Nao integraremos scraping, Gemini ou banco no primeiro arquivo. Primeiro
provaremos o fluxo e as transicoes do grafo.
