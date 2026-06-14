# Módulo de Scraping — Arquitetura Corrigida do Sistema

## 1. Objetivo do módulo

O módulo `scraping` é responsável por coletar conteúdo público da web e produzir um resultado bruto confiável para as próximas etapas do sistema.

Ele deve:

```txt
receber uma URL ou uma fonte
criar e consultar jobs de scraping
executar estratégias de coleta
validar tecnicamente o resultado
validar a qualidade textual
calcular scores de qualidade
decidir entre aceitar, aplicar fallback, pedir revisão simples por LLM, encaminhar para investigação com agentes ou rejeitar
registrar todas as tentativas
salvar o conteúdo bruto aprovado
disponibilizar o resultado para o módulo de ingestion
```

Ele não deve:

```txt
executar o worker dentro do módulo
normalizar profundamente os dados
extrair todos os campos estruturados da startup
dividir documentos em chunks
gerar embeddings
executar RAG
recomendar tecnologias NVIDIA
```

A divisão principal é:

```txt
scraping
→ coleta e garante qualidade mínima do conteúdo bruto

ingestion
→ limpa, normaliza, estrutura e prepara o conteúdo

rag
→ recupera evidências e gera respostas com contexto

recommendations
→ gera recomendações NVIDIA
```

---

# 2. Worker fora do módulo

O worker não fica dentro de `modules/scraping`.

Ele é um processo separado da API e dos módulos de negócio.

Estrutura correta:

```txt
project/
├── apps/
│   └── api/
│       └── src/
│           └── modules/
│               └── scraping/
│                   ├── presentation/
│                   ├── application/
│                   ├── domain/
│                   ├── infrastructure/
│                   └── factories/
│
└── workers/
    └── scraper_worker/
        ├── run.py
        └── tasks.py
```

A regra é:

```txt
Worker executa.
Módulo sabe fazer.
```

O worker recebe um `job_id` da fila e chama o caso de uso do módulo.

Exemplo:

```python
# workers/scraper_worker/tasks.py

from uuid import UUID

from apps.api.src.modules.scraping.factories.scraping_factory import (
    ScrapingFactory,
)


async def execute_scraping_job(job_id: str) -> None:
    use_case = ScrapingFactory.create_execute_scraping_job()
    await use_case.execute(UUID(job_id))
```

O worker não deve conter:

```txt
BeautifulSoup
Playwright
Firecrawl
SQL
validação de qualidade
score
fallback
regra de status
```

Essas responsabilidades pertencem ao módulo `scraping`.

---

# 3. Arquitetura interna do módulo

A arquitetura recomendada é:

```txt
Presentation
↓
Application
↓
Domain

Infrastructure
→ implementa os contratos usados pela aplicação
```

Responsabilidades:

```txt
Presentation
→ entrada e saída HTTP

Application
→ casos de uso e coordenação da pipeline

Domain
→ entidades, regras, estados, políticas e contratos

Infrastructure
→ scraping técnico, banco, APIs externas, fila e validações técnicas
```

Essa organização é mais adequada que MVC puro porque o módulo possui:

```txt
jobs assíncronos
fila
worker externo
fallback entre estratégias
integrações externas
validação em múltiplos níveis
persistência de tentativas
revisão semântica com IA
```

Existe uma equivalência aproximada com MVC:

```txt
Controller
→ presentation/routes

Service
→ application/use_cases e application/services

Model
→ domain/entities e infrastructure/database/models

View
→ schemas de resposta JSON
```

O nome mais preciso é:

```txt
arquitetura em camadas dentro de um monolito modular
```

---

# 4. Estrutura completa recomendada

```txt
modules/
└── scraping/
    ├── presentation/
    │   ├── routes/
    │   │   ├── router.py
    │   │   ├── jobs_routes.py
    │   │   └── results_routes.py
    │   │
    │   ├── schemas/
    │   │   ├── requests.py
    │   │   └── responses.py
    │   │
    │   ├── dependencies.py
    │   └── exception_handlers.py
    │
    ├── application/
    │   ├── use_cases/
    │   │   ├── create_scraping_job.py
    │   │   ├── execute_scraping_job.py
    │   │   ├── get_scraping_job.py
    │   │   ├── get_scraping_result.py
    │   │   ├── retry_scraping_job.py
    │   │   └── cancel_scraping_job.py
    │   │
    │   ├── pipelines/
    │   │   └── scraping_pipeline.py
    │   │
    │   ├── services/
    │   │   ├── quality_scoring_service.py
    │   │   ├── semantic_confidence_service.py
    │   │   ├── semantic_validation_service.py
    │   │   └── agent_review_service.py
    │   │
    │   ├── selectors/
    │   │   └── scraping_strategy_selector.py
    │   │
    │   ├── dto/
    │   │   ├── scraping_input.py
    │   │   ├── scraping_output.py
    │   │   ├── deterministic_validation_result.py
    │   │   └── semantic_validation_result.py
    │   │
    │   ├── ports/
    │   │   ├── scraper.py
    │   │   ├── crawler.py
    │   │   ├── deterministic_validator.py
    │   │   ├── semantic_validator.py
    │   │   ├── semantic_investigator.py
    │   │   └── task_dispatcher.py
    │   │
    │   └── public/
    │       └── scraping_result_reader.py
    │
    ├── domain/
    │   ├── entities/
    │   │   ├── scraping_job.py
    │   │   ├── scraping_result.py
    │   │   └── scraping_attempt.py
    │   │
    │   ├── value_objects/
    │   │   ├── scraping_url.py
    │   │   └── quality_score.py
    │   │
    │   ├── enums/
    │   │   ├── job_status.py
    │   │   ├── attempt_status.py
    │   │   ├── scraping_method.py
    │   │   ├── validation_decision.py
    │   │   └── semantic_review_decision.py
    │   │
    │   ├── repositories/
    │   │   ├── scraping_job_repository.py
    │   │   ├── scraping_result_repository.py
    │   │   └── scraping_attempt_repository.py
    │   │
    │   ├── policies/
    │   │   ├── content_acceptance_policy.py
    │   │   ├── fallback_policy.py
    │   │   └── llm_review_policy.py
    │   │
    │   └── exceptions.py
    │
    ├── infrastructure/
    │   ├── database/
    │   │   ├── models/
    │   │   ├── mappers/
    │   │   └── repositories/
    │   │
    │   ├── scrapers/
    │   │   ├── generic/
    │   │   │   ├── beautifulsoup_scraper.py
    │   │   │   ├── playwright_scraper.py
    │   │   │   ├── trafilatura_scraper.py
    │   │   │   └── firecrawl_scraper.py
    │   │   │
    │   │   ├── sources/
    │   │   │   └── example_source/
    │   │   │       ├── scraper.py
    │   │   │       ├── parser.py
    │   │   │       └── selectors.py
    │   │   │
    │   │   └── crawlers/
    │   │       └── startup_directory_crawler.py
    │   │
    │   ├── clients/
    │   │   ├── http_client.py
    │   │   ├── playwright_client.py
    │   │   ├── firecrawl_client.py
    │   │   └── llm_client.py
    │   │
    │   ├── validators/
    │   │   ├── technical_validator.py
    │   │   ├── textual_validator.py
    │   │   ├── evidence_signal_validator.py
    │   │   └── composite_deterministic_validator.py
    │   │
    │   ├── semantic_validators/
    │   │   └── llm_semantic_validator.py
    │   │
    │   ├── agent_adapters/
    │   │   └── agents_semantic_investigator.py
    │   │
    │   └── queue/
    │       └── dramatiq_task_dispatcher.py
    │
    ├── factories/
    │   └── scraping_factory.py
    │
    └── tests/
        ├── unit/
        ├── integration/
        └── fixtures/
```

---

# 5. Fluxo completo da validação

O fluxo deve separar claramente:

```txt
coleta
validação determinística
score
decisão
fallback
revisão por IA
persistência
```

Fluxo:

```txt
Scraper executa
↓
Validação técnica
↓
Validação textual
↓
Sinais evidenciais básicos
↓
Cálculo dos scores
↓
Políticas de decisão
```

Depois disso, existem cinco decisões:

```txt
ACCEPT
→ conteúdo claramente válido

FALLBACK
→ coleta ruim; tentar outra tecnologia

LLM_REVIEW
→ conteúdo tecnicamente bom, mas semanticamente ambíguo

AGENT_REVIEW
→ a LLM simples não conseguiu decidir com segurança ou é necessária investigação em múltiplas etapas

REJECT
→ conteúdo não deve ser aceito e não vale novo fallback
```

A ordem correta é:

```txt
validação determinística
↓
validação simples com LLM, somente quando necessária
↓
investigação com agentes, somente quando a LLM continuar incerta
```

---

# 6. Validação técnica

A validação técnica verifica se a coleta funcionou corretamente.

Critérios:

```txt
status HTTP
timeout
erro de conexão
content-type
resposta vazia
tamanho do HTML
redirecionamento excessivo
URL final
captcha
bloqueio
login obrigatório
```

Exemplos de regras:

```txt
status_code >= 400
→ falha técnica

captcha detectado
→ blocked

source_url ausente
→ resultado sem rastreabilidade

html_length muito pequeno
→ possível falha de coleta
```

Essas regras devem ser determinísticas.

Não é necessário chamar IA para verificar status HTTP ou timeout.

---

# 7. Validação textual

A validação textual verifica a qualidade básica do texto extraído.

Critérios:

```txt
quantidade de caracteres
quantidade de palavras
densidade textual
repetição
boilerplate
proporção de links
idioma
duplicidade
presença de título
```

Exemplos iniciais:

```txt
clean_text_length < 300
→ texto muito fraco

word_count < 80
→ pouco conteúdo útil

boilerplate_ratio alto
→ muito menu, rodapé ou navegação

duplicate_ratio alto
→ texto repetitivo
```

Esses limites são iniciais e devem ser ajustados com testes reais.

---

# 8. Sinais evidenciais básicos

Antes de chamar IA, o sistema pode calcular sinais simples por código.

Exemplos:

```txt
nome da startup aparece
palavras relacionadas ao produto aparecem
termos de IA aparecem
URL é de fonte oficial
data de publicação existe
descrição de produto está presente
```

Isso gera um `evidence_score` inicial.

Esse score não substitui a validação semântica com IA.

Ele serve para decidir se a IA deve ser chamada.

---

# 9. Scores de qualidade

A validação determinística gera três scores:

```txt
technical_score
text_score
evidence_score
```

Fórmula inicial:

```txt
quality_score =
    technical_score * 0.30
    + text_score * 0.30
    + evidence_score * 0.40
```

Pesos iniciais:

```txt
técnico: 30%
textual: 30%
evidencial: 40%
```

A parte evidencial recebe maior peso porque o objetivo não é apenas obter texto, mas obter conteúdo útil para analisar startups.

Exemplo de DTO:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DeterministicValidationResult:
    technical_score: float
    text_score: float
    evidence_score: float
    quality_score: float
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

---

# 10. Score não decide tudo sozinho

O sistema não deve usar somente a média.

Alguns problemas são bloqueadores.

Exemplos:

```txt
captcha
status 403
URL sem rastreabilidade
conteúdo vazio
login obrigatório
conteúdo de outra empresa
```

Mesmo que a média fique alta, um bloqueador pode impedir a aceitação.

Exemplo:

```python
if "captcha" in result.problems:
    return ValidationDecision.FALLBACK
```

A decisão final deve combinar:

```txt
scores
+
problemas bloqueadores
+
políticas
```

---

# 11. Critérios iniciais de decisão

Sugestão inicial:

```txt
quality_score >= 0.75
e nenhum problema bloqueador
→ ACCEPT

0.45 <= quality_score < 0.75
e conteúdo técnico/textual suficiente
→ LLM_REVIEW

LLM retorna baixa confiança, conflito ou necessidade de novas fontes
→ AGENT_REVIEW

quality_score < 0.45
e existe estratégia alternativa
→ FALLBACK

quality_score < 0.45
e não existe alternativa útil
→ REJECT
```

Mais importante que o valor exato é a lógica:

```txt
muito ruim
→ não chama IA

muito bom
→ aceita sem IA

intermediário ou ambíguo
→ chama LLM simples

LLM simples continua incerta
→ chama agentes
```

---

# 12. Política de aceitação

Arquivo:

```txt
domain/policies/content_acceptance_policy.py
```

Responsável por decidir se o conteúdo pode ser aceito sem IA.

Exemplo:

```python
class ContentAcceptancePolicy:

    MINIMUM_SCORE = 0.75

    BLOCKING_PROBLEMS = {
        "captcha",
        "empty_content",
        "missing_source_url",
        "login_required",
    }

    def accepts(self, result) -> bool:
        if self.BLOCKING_PROBLEMS.intersection(result.problems):
            return False

        return result.quality_score >= self.MINIMUM_SCORE
```

---

# 13. Política de fallback

Arquivo:

```txt
domain/policies/fallback_policy.py
```

O fallback deve ser usado quando o problema pode ser corrigido por outra estratégia de coleta.

Exemplos:

```txt
BeautifulSoup retornou pouco conteúdo
→ tenta Playwright ou Trafilatura

página depende de JavaScript
→ tenta Playwright

texto tem muito boilerplate
→ tenta Trafilatura ou Firecrawl

HTML incompleto
→ tenta Playwright

conteúdo bloqueado
→ registra blocked e tenta apenas alternativas permitidas
```

Não use fallback quando:

```txt
a página está boa, mas o significado é ambíguo
a fonte fala de outra empresa
o conteúdo é irrelevante para o objetivo
```

Nesses casos, pode ser necessário:

```txt
LLM_REVIEW
ou
REJECT
ou
buscar outra fonte
```

Exemplo:

```python
class FallbackPolicy:

    FALLBACK_PROBLEMS = {
        "javascript_required",
        "insufficient_text",
        "high_boilerplate",
        "empty_content",
        "incomplete_html",
    }

    def should_fallback(
        self,
        result,
        has_next_strategy: bool,
    ) -> bool:
        if not has_next_strategy:
            return False

        return bool(
            self.FALLBACK_PROBLEMS.intersection(result.problems)
        )
```

---

# 14. Ordem das estratégias

A ordem não deve ser fixa para toda URL.

Exemplos:

```txt
artigo ou notícia
→ Trafilatura
→ BeautifulSoup
→ Playwright
→ Firecrawl

site HTML simples
→ BeautifulSoup
→ Trafilatura
→ Playwright
→ Firecrawl

site conhecido por depender de JavaScript
→ Playwright
→ Firecrawl

fonte conhecida com scraper próprio
→ scraper específico
→ Playwright
→ Firecrawl
```

O `ScrapingStrategySelector` decide a ordem.

---

# 15. Validação semântica em dois níveis

A validação semântica deve possuir dois níveis:

```txt
Nível 1
→ validação simples com LLM

Nível 2
→ investigação com agentes
```

A LLM simples sempre vem antes do agente.

Os agentes só entram quando a LLM não consegue decidir com segurança ou quando é necessário executar uma investigação com múltiplas etapas e ferramentas.

Fluxo:

```txt
Conteúdo passou na validação técnica e textual
↓
Conteúdo ainda é semanticamente ambíguo
↓
Chama LLM simples
↓
LLM consegue decidir com confiança suficiente?
├── Sim → ACCEPT ou REJECT
└── Não → AGENT_REVIEW
```

---

# 16. Nível 1 — Validação simples com LLM

A LLM simples analisa somente o conteúdo atual e o contexto mínimo da coleta.

Ela entra quando:

```txt
a coleta passou tecnicamente
o texto tem qualidade mínima
o conteúdo parece potencialmente relevante
a evidência ainda é ambígua
```

Exemplos de ambiguidade:

```txt
menciona IA de forma genérica
fala em automação, mas não se sabe se é IA
o nome da empresa aparece, mas pode haver homônimo
o texto é grande, mas não apresenta evidência concreta
a fonte parece relevante, mas não descreve claramente o produto
```

A regra é:

```txt
Código valida qualidade técnica.
Código valida qualidade textual.
Código calcula sinais básicos.
LLM interpreta semanticamente um conteúdo.
Pipeline decide o próximo passo.
```

A LLM simples não deve:

```txt
buscar outras páginas
navegar pela web
executar várias ferramentas
orquestrar outros módulos
escolher BeautifulSoup, Playwright ou Firecrawl
```

---

# 17. Diferença entre quality_score e semantic_confidence

Os dois valores medem coisas diferentes.

```txt
quality_score
→ mede a qualidade objetiva da coleta

semantic_confidence
→ mede a segurança da interpretação semântica
```

O `quality_score` considera:

```txt
qualidade técnica
qualidade textual
sinais evidenciais básicos
```

O `semantic_confidence` considera:

```txt
correspondência com a startup
clareza da evidência
confiabilidade da fonte
especificidade da afirmação
completude do contexto
contradições encontradas
```

A tecnologia usada para coletar não determina a confiabilidade da fonte.

Exemplo:

```txt
Playwright extrai perfeitamente uma página pouco confiável.

qualidade técnica da coleta = alta
confiabilidade da fonte = baixa
```

Outro exemplo:

```txt
BeautifulSoup extrai uma documentação oficial.

qualidade técnica da coleta = alta
confiabilidade da fonte = alta
```

Portanto:

```txt
scraping_method
→ como o conteúdo foi coletado

source_reliability
→ de onde a informação veio
```

---

# 18. Fatores do semantic_confidence

## 18.1 Correspondência com a startup

Campo:

```txt
startup_match_score
```

Pergunta:

```txt
O conteúdo realmente fala da startup analisada?
```

Pode considerar:

```txt
nome completo
domínio oficial
produto
fundadores
setor
localização
identificadores conhecidos
```

Esse fator recebe peso alto porque uma evidência excelente sobre a empresa errada não possui valor para a análise.

---

## 18.2 Clareza da evidência

Campo:

```txt
evidence_clarity_score
```

Pergunta:

```txt
O texto apresenta uma evidência clara ou apenas uma afirmação vaga?
```

Exemplo fraco:

```txt
“Usamos inteligência artificial para transformar negócios.”
```

Exemplo mais claro:

```txt
“A plataforma utiliza modelos de linguagem para classificar chamados e gerar respostas para equipes de suporte.”
```

---

## 18.3 Confiabilidade da fonte

Campo:

```txt
source_reliability_score
```

Pergunta:

```txt
Quanto podemos confiar na origem da informação?
```

Escala inicial possível:

```txt
documentação oficial
→ alta

site oficial da empresa
→ alta ou média-alta

notícia de veículo reconhecido
→ média-alta

site de aceleradora ou investidor
→ média

diretório de startups
→ média ou baixa

post sem autoria
→ baixa

agregador automático
→ baixa
```

Fonte oficial é confiável para confirmar o que a empresa declara, mas pode conter linguagem comercial. Por isso, confiabilidade da fonte não substitui clareza e especificidade.

---

## 18.4 Especificidade da afirmação

Campo:

```txt
statement_specificity_score
```

Pergunta:

```txt
A afirmação possui detalhes verificáveis?
```

Detalhes que aumentam o score:

```txt
tipo de modelo
tipo de dado
tarefa executada
parte do produto
infraestrutura
caso de uso
métrica
cliente
resultado
```

---

## 18.5 Completude do contexto

Campo:

```txt
context_completeness_score
```

Pergunta:

```txt
Existe informação suficiente para tomar uma decisão?
```

Um trecho pode ser verdadeiro, mas incompleto.

Exemplo:

```txt
“Nossa solução usa machine learning.”
```

Ainda faltam respostas como:

```txt
onde é usado
para qual tarefa
se é parte central do produto
se está em produção
se é apenas um plano futuro
```

---

## 18.6 Penalidade por contradições

Campo:

```txt
contradiction_penalty
```

Pergunta:

```txt
Existem informações conflitantes?
```

Contradições devem reduzir a confiança e podem obrigar o encaminhamento para agentes.

---

# 19. Cálculo do semantic_confidence

Uma fórmula inicial recomendada é:

```txt
semantic_confidence =
    startup_match_score * 0.25
    + evidence_clarity_score * 0.25
    + source_reliability_score * 0.20
    + statement_specificity_score * 0.15
    + context_completeness_score * 0.15
    - contradiction_penalty
```

Justificativa dos pesos:

```txt
startup_match: 25%
→ não adianta ter uma boa evidência sobre a empresa errada

evidence_clarity: 25%
→ a evidência precisa realmente sustentar a afirmação

source_reliability: 20%
→ a origem influencia a credibilidade

statement_specificity: 15%
→ detalhes concretos reduzem ambiguidade

context_completeness: 15%
→ contexto incompleto aumenta o risco
```

Os pesos são um ponto inicial e devem ser calibrados com exemplos reais revisados manualmente.

É melhor pedir à LLM os fatores separados e calcular a confiança no sistema do que aceitar cegamente um único número produzido pela própria LLM.

Exemplo de saída da LLM:

```json
{
  "startup_match_score": 0.95,
  "evidence_clarity_score": 0.78,
  "source_reliability_score": 0.85,
  "statement_specificity_score": 0.72,
  "context_completeness_score": 0.68,
  "contradiction_detected": false,
  "decision": "accepted",
  "reason": "O texto descreve uma aplicação concreta de IA no produto."
}
```

O sistema calcula o `semantic_confidence` com base nesses fatores.

---

# 20. Limites de confiança

Valores iniciais recomendados:

```txt
semantic_confidence >= 0.80
→ a decisão da LLM pode ser aceita automaticamente, desde que não existam bloqueadores

0.60 <= semantic_confidence < 0.80
→ AGENT_REVIEW

semantic_confidence < 0.60
→ AGENT_REVIEW ou REJECT, conforme a relevância e a qualidade da fonte
```

Uma regra conservadora para a primeira versão é:

```txt
0.80 ou mais
→ aceitar a decisão da LLM

abaixo de 0.80
→ encaminhar para agente

abaixo de 0.40 e conteúdo claramente irrelevante
→ rejeitar sem agente
```

A confiança não decide sozinha.

Mesmo com confiança alta, deve haver revisão por agente quando existir:

```txt
contradição
fonte muito fraca
identidade incerta da startup
informações incompatíveis
necessidade de buscar outras fontes
```

---

# 21. Saída estruturada da LLM simples

Decisões permitidas:

```txt
accepted
rejected
needs_agent_review
```

DTO conceitual:

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SemanticValidationResult:
    startup_match_score: float
    evidence_clarity_score: float
    source_reliability_score: float
    statement_specificity_score: float
    context_completeness_score: float
    contradiction_detected: bool
    semantic_confidence: float
    decision: Literal[
        "accepted",
        "rejected",
        "needs_agent_review",
    ]
    reason: str
```

---

# 22. Nível 2 — Investigação com agentes

Os agentes entram somente quando a validação simples com LLM não é suficiente.

Exemplos:

```txt
a LLM retornou baixa confiança
a LLM encontrou informações conflitantes
é necessário buscar outras fontes
é necessário comparar vários documentos
é necessário consultar o RAG
é necessário validar a identidade da startup
é necessário coletar novas evidências
```

O agente pode:

```txt
buscar outras fontes
solicitar novos scrapings
consultar documentos existentes
consultar o RAG
comparar evidências
identificar contradições
produzir uma decisão final fundamentada
```

O agente não deve ser usado para:

```txt
status HTTP
timeout
texto vazio
captcha
boilerplate
problemas resolvidos por fallback técnico
```

Regra:

```txt
Fallback corrige problema de coleta.
LLM simples interpreta um conteúdo.
Agente investiga quando um único conteúdo não é suficiente.
```

---

# 23. Integração com o módulo agents

O agente não deve ser implementado dentro do módulo `scraping`.

O módulo `scraping` chama um contrato público do módulo `agents`.

Fluxo:

```txt
scraping
↓
SemanticInvestigator
↓
contrato público do módulo agents
↓
grafo de investigação
↓
resultado estruturado
```

Interface dentro de scraping:

```txt
application/ports/semantic_investigator.py
```

Adaptador:

```txt
infrastructure/agent_adapters/
└── agents_semantic_investigator.py
```

O módulo `scraping` conhece apenas o contrato público.

Ele não deve importar nodes, graphs ou arquivos internos do módulo `agents`.

Decisões finais possíveis do agente:

```txt
accepted
rejected
needs_more_sources
```

Caso o agente conclua `needs_more_sources`, o fluxo global pode criar novos jobs de scraping pelos contratos públicos apropriados.

---

# 24. Pipeline corrigida

Fluxo da pipeline:

```python
class ScrapingPipeline:

    def __init__(
        self,
        strategy_selector,
        deterministic_validator,
        scoring_service,
        acceptance_policy,
        fallback_policy,
        llm_review_policy,
        semantic_validator,
        semantic_investigator,
        attempt_repository,
    ):
        self.strategy_selector = strategy_selector
        self.deterministic_validator = deterministic_validator
        self.scoring_service = scoring_service
        self.acceptance_policy = acceptance_policy
        self.fallback_policy = fallback_policy
        self.llm_review_policy = llm_review_policy
        self.semantic_validator = semantic_validator
        self.semantic_investigator = semantic_investigator
        self.attempt_repository = attempt_repository

    async def execute(self, context):
        strategies = self.strategy_selector.select(context)

        for index, scraper in enumerate(strategies):
            has_next_strategy = index < len(strategies) - 1

            attempt = ScrapingAttempt.start(
                job_id=context.job_id,
                url=context.url,
                method=scraper.method,
            )

            try:
                output = await scraper.scrape(
                    ScrapingInput(url=context.url)
                )

                deterministic = (
                    await self.deterministic_validator.validate(output)
                )

                deterministic = self.scoring_service.calculate(
                    deterministic
                )

                if self.acceptance_policy.accepts(deterministic):
                    attempt.accept(
                        quality_score=deterministic.quality_score
                    )
                    await self.attempt_repository.save(attempt)
                    return output

                if self.llm_review_policy.requires_review(
                    deterministic
                ):
                    semantic = await self.semantic_validator.validate(
                        self._build_semantic_input(
                            context,
                            output,
                            deterministic,
                        )
                    )

                    if semantic.decision == "accepted":
                        attempt.accept(
                            quality_score=deterministic.quality_score,
                            semantic_confidence=semantic.confidence,
                        )
                        await self.attempt_repository.save(attempt)
                        return output

                    if (
                        semantic.decision == "needs_agent_review"
                        or semantic.semantic_confidence < 0.80
                    ):
                        investigation = (
                            await self.semantic_investigator.investigate(
                                self._build_investigation_input(
                                    context,
                                    output,
                                    deterministic,
                                    semantic,
                                )
                            )
                        )

                        if investigation.decision == "accepted":
                            attempt.accept(
                                quality_score=deterministic.quality_score,
                                semantic_confidence=(
                                    semantic.semantic_confidence
                                ),
                                agent_reviewed=True,
                            )
                            await self.attempt_repository.save(attempt)
                            return output

                        if investigation.decision == "needs_more_sources":
                            attempt.finish_needs_more_sources(
                                investigation.reason
                            )
                            await self.attempt_repository.save(attempt)
                            raise MoreSourcesRequiredError(
                                investigation.reason
                            )

                        attempt.reject(investigation.reason)
                        await self.attempt_repository.save(attempt)
                        raise ContentRejectedError(
                            investigation.reason
                        )

                    attempt.reject(semantic.reason)
                    await self.attempt_repository.save(attempt)
                    raise ContentRejectedError(
                        semantic.reason
                    )

                if self.fallback_policy.should_fallback(
                    deterministic,
                    has_next_strategy,
                ):
                    attempt.finish_fallback(
                        problems=deterministic.problems,
                        quality_score=deterministic.quality_score,
                    )
                    await self.attempt_repository.save(attempt)
                    continue

                attempt.reject(
                    "Conteúdo inválido e sem fallback aplicável."
                )
                await self.attempt_repository.save(attempt)
                raise ContentRejectedError()

            except RecoverableScrapingError as error:
                attempt.fail(str(error))
                await self.attempt_repository.save(attempt)

                if has_next_strategy:
                    continue

                raise ScrapingFailedError() from error

        raise ScrapingFailedError(
            "Nenhuma estratégia produziu conteúdo válido."
        )
```

---

# 25. Persistência das tentativas

Cada tentativa deve ser salva.

Exemplo:

```txt
tentativa 1
method = beautifulsoup
decision = fallback
quality_score = 0.31
problems = insufficient_text

tentativa 2
method = playwright
decision = llm_review
quality_score = 0.67

tentativa 2 — revisão semântica
decision = accepted
semantic_confidence = 0.86
```

Tabela sugerida:

```txt
scraping_attempts
```

Campos:

```txt
id
job_id
url
method
status
decision
technical_score
text_score
evidence_score
quality_score
semantic_confidence
agent_reviewed
agent_decision
problems
warnings
error_message
started_at
finished_at
```

Benefícios:

```txt
debug
auditoria
métricas
análise de custo
melhoria do selector
identificação de fontes problemáticas
```

---

# 26. Entidades principais

## ScrapingJob

Representa o processo completo.

Campos:

```txt
id
url
startup_id
status
result_id
error_message
created_at
started_at
finished_at
```

Status:

```txt
pending
running
completed
failed
cancelled
```

Regras:

```txt
pending → running
running → completed
running → failed
pending → cancelled
running → cancelled
```

Transições inválidas devem ser bloqueadas.

---

## ScrapingResult

Representa o conteúdo bruto aprovado.

Campos:

```txt
id
job_id
url
final_url
title
raw_html
raw_text
method
status_code
technical_score
text_score
evidence_score
quality_score
semantic_validation_status
semantic_confidence
content_hash
metadata
created_at
```

---

## ScrapingAttempt

Representa uma tentativa de coleta e validação.

Campos:

```txt
id
job_id
method
status
decision
scores
problems
error_message
timestamps
```

---

# 27. Scrapers genéricos

Estrutura:

```txt
infrastructure/scrapers/generic/
```

## BeautifulSoup

Uso:

```txt
HTML estático
página simples
baixo custo
```

## Playwright

Uso:

```txt
JavaScript
conteúdo dinâmico
interação
scroll
espera por seletor
```

## Trafilatura

Uso:

```txt
artigos
notícias
blogs
texto principal
```

## Firecrawl

Uso:

```txt
fallback externo
conteúdo limpo
páginas mais difíceis
```

Cuidados:

```txt
custo
timeout
limites
dependência externa
```

---

# 28. Scrapers específicos de fontes

Estrutura:

```txt
infrastructure/scrapers/sources/
```

Use quando uma fonte possui HTML conhecido.

Exemplo:

```txt
startup_portal/
├── scraper.py
├── parser.py
└── selectors.py
```

Importante:

```txt
Playwright é uma tecnologia.
Startup Portal é uma fonte.
```

Um scraper de fonte pode usar Playwright ou BeautifulSoup internamente.

---

# 29. Crawlers

Crawlers ficam dentro da infraestrutura do módulo porque são mecanismos técnicos de coleta.

Estrutura:

```txt
infrastructure/scrapers/crawlers/
```

Diferença:

```txt
Scraper
→ coleta uma página

Crawler
→ percorre várias páginas e links
```

Scrapy é indicado para:

```txt
paginação
muitas páginas
concorrência
crawling estruturado
```

Um crawler pode ter contrato diferente de um scraper comum.

---

# 30. Fila e dispatcher

O processo worker está fora.

Dentro do módulo pode existir apenas o adaptador que envia mensagens para a fila:

```txt
infrastructure/queue/
└── dramatiq_task_dispatcher.py
```

Exemplo:

```python
class DramatiqTaskDispatcher:

    async def dispatch(self, job_id) -> None:
        execute_scraping_job_task.send(str(job_id))
```

O worker consome a fila e chama o módulo.

Fluxo:

```txt
API
↓
CreateScrapingJob
↓
TaskDispatcher
↓
Fila
↓
Worker externo
↓
ExecuteScrapingJob
↓
ScrapingPipeline
```

---

# 31. Casos de uso

## CreateScrapingJob

Responsável por:

```txt
validar URL
verificar duplicidade
criar job pending
salvar
enviar job_id para fila
```

## ExecuteScrapingJob

Responsável por:

```txt
buscar job
mudar para running
executar pipeline
salvar resultado
mudar para completed
tratar falha
```

## RetryScrapingJob

Responsável por:

```txt
verificar se retry é permitido
limpar erro anterior
criar nova execução ou reabrir job
enviar novamente à fila
```

## GetScrapingJob

Responsável por consultar o status.

## GetScrapingResult

Responsável por consultar o resultado aprovado.

---

# 32. Comunicação com ingestion

O módulo `ingestion` não deve acessar models ou tabelas internas de `scraping` diretamente.

Errado:

```python
from modules.scraping.infrastructure.database.models import (
    ScrapingResultModel
)
```

Certo:

```txt
ingestion
↓
ScrapingResultReader
↓
ScrapingResultRepository
```

Contrato público:

```txt
application/public/scraping_result_reader.py
```

Exemplo:

```python
class ScrapingResultReader:

    def __init__(self, result_repository):
        self.result_repository = result_repository

    async def get_raw_document(self, result_id):
        result = await self.result_repository.get_by_id(
            result_id
        )

        return RawScrapingDocumentDTO(
            id=result.id,
            url=result.url,
            raw_html=result.raw_html,
            raw_text=result.raw_text,
            quality_score=result.quality_score,
            metadata=result.metadata,
        )
```

Outra opção futura:

```txt
ScrapingCompleted
↓
evento
↓
ingestion inicia
```

Para o começo, o serviço público é mais simples.

---

# 33. Limite entre scraping e validação semântica

Há uma decisão arquitetural importante.

## Dentro de scraping

Faz sentido manter:

```txt
validação técnica
validação textual
score básico evidencial
fallback
revisão semântica leve
```

A revisão semântica leve responde:

```txt
esse conteúdo é sobre a startup certa?
há evidência mínima útil?
vale seguir para ingestion?
```

## Fora de scraping

Análises profundas ficam em ingestion ou agents:

```txt
classificação AI-native
extração estruturada completa
maturidade técnica
recomendação NVIDIA
validação cruzada entre múltiplas fontes
```

Assim, a IA dentro de scraping atua como filtro final, não como analista completo da startup.

---

# 34. Banco de dados

Tabelas:

```txt
scraping_jobs
scraping_results
scraping_attempts
```

## scraping_jobs

```txt
id
startup_id
url
status
result_id
error_message
created_at
started_at
finished_at
```

## scraping_results

```txt
id
job_id
url
final_url
title
raw_html
raw_text
method
status_code
technical_score
text_score
evidence_score
quality_score
semantic_validation_status
semantic_confidence
content_hash
metadata
created_at
```

## scraping_attempts

```txt
id
job_id
method
status
decision
technical_score
text_score
evidence_score
quality_score
semantic_confidence
agent_reviewed
agent_decision
problems
warnings
error_message
started_at
finished_at
```

---

# 35. Segurança

## SSRF

Bloquear:

```txt
localhost
127.0.0.1
0.0.0.0
IPs privados
metadata de cloud
file://
ftp://
```

Permitir apenas:

```txt
http://
https://
```

Validar também redirects.

## Limites

Definir:

```txt
timeout
tamanho máximo
máximo de redirects
máximo de tentativas
máximo de páginas
concorrência
```

## Segredos

Guardar em:

```txt
.env local
secret manager em produção
```

Nunca no código.

---

# 36. Logs e métricas

Logs:

```txt
job criado
job iniciado
estratégia escolhida
tentativa iniciada
scores calculados
fallback aplicado
LLM simples chamada
decisão da LLM
agente chamado
decisão do agente
resultado aceito
job concluído
job falhou
```

Métricas:

```txt
taxa de sucesso por estratégia
taxa de fallback
taxa de chamada da LLM simples
taxa de aceitação pela LLM
taxa de escalonamento para agentes
taxa de aceitação após investigação
tempo médio
custo por estratégia
custo de IA
taxa de captcha
qualidade média
```

A IA deve ser monitorada porque adiciona custo e latência.

---

# 37. Testes

## Domínio

```txt
transições de job
score entre 0 e 1
política de aceitação
política de fallback
política de revisão por IA
```

## Application

```txt
pipeline aceita conteúdo bom
pipeline chama fallback para conteúdo ruim
pipeline chama LLM apenas em caso ambíguo
pipeline chama agente apenas quando a LLM continua incerta
pipeline rejeita resultado da LLM ou do agente
pipeline salva tentativas
```

## Infrastructure

```txt
BeautifulSoup extrai corretamente
Playwright trata timeout
validator detecta captcha
LLM validator valida saída estruturada
adaptador de agents retorna saída estruturada
repository persiste entidades
```

## Integração

```txt
API cria job
dispatcher envia à fila
worker externo executa
resultado é salvo
status muda
```

---

# 38. Regras de dependência

Permitido:

```txt
presentation → application
application → domain
infrastructure → application
infrastructure → domain
factories → conecta tudo
worker externo → application/factory
```

Proibido:

```txt
domain → infrastructure
domain → FastAPI
domain → SQLAlchemy
application → Playwright
application → BeautifulSoup
scraper → repository
validator → route
worker → implementação interna de scraper
```

---

# 39. Estrutura inicial para começar

Não crie tudo no primeiro dia.

Comece:

```txt
modules/
└── scraping/
    ├── presentation/
    │   ├── routes.py
    │   ├── schemas.py
    │   └── dependencies.py
    │
    ├── application/
    │   ├── create_scraping_job.py
    │   ├── execute_scraping_job.py
    │   ├── scraping_pipeline.py
    │   ├── quality_scoring_service.py
    │   ├── strategy_selector.py
    │   └── dto.py
    │
    ├── domain/
    │   ├── entities.py
    │   ├── enums.py
    │   ├── policies.py
    │   ├── repositories.py
    │   └── exceptions.py
    │
    ├── infrastructure/
    │   ├── database.py
    │   ├── scrapers/
    │   │   ├── beautifulsoup_scraper.py
    │   │   └── playwright_scraper.py
    │   ├── deterministic_validator.py
    │   ├── llm_semantic_validator.py
    │   └── task_dispatcher.py
    │
    ├── factory.py
    └── tests/
```

E fora:

```txt
workers/
└── scraper_worker/
    ├── run.py
    └── tasks.py
```

---

# 40. Primeira entrega vertical

```txt
1. POST /scraping/jobs
2. criar job pending
3. enviar job_id à fila
4. worker externo recebe
5. ExecuteScrapingJob inicia
6. BeautifulSoup coleta
7. validação técnica e textual
8. score calculado
9. aceitar ou tentar Playwright
10. chamar LLM apenas se ambíguo
11. chamar agente apenas se a LLM continuar incerta
12. salvar resultado
13. marcar completed ou failed
14. consultar status e resultado
```

---

# 41. Resumo final

```txt
Route
→ recebe HTTP

Use case
→ coordena operação

Pipeline
→ coordena scraping, validação, fallback, LLM e escalonamento para agentes

Selector
→ escolhe ordem das estratégias

Scraper
→ coleta tecnicamente

Validator determinístico
→ verifica qualidade objetiva

Scoring service
→ calcula scores

Acceptance policy
→ decide aceitação direta

Fallback policy
→ decide nova tecnologia

LLM review policy
→ decide quando chamar IA

Semantic validator
→ interpreta semanticamente um conteúdo

Semantic investigator
→ chama agentes quando a LLM simples não é suficiente

Repository
→ persiste jobs, resultados e tentativas

Task dispatcher
→ envia job à fila

Worker externo
→ chama o caso de uso
```

Regra final:

```txt
Worker fica fora do módulo.
Fila conecta API e worker.
Módulo contém a lógica.
Fallback resolve problema de coleta.
LLM simples resolve ambiguidades locais.
Agentes investigam ambiguidades que exigem múltiplas fontes ou ferramentas.
Score ajuda a decidir, mas não substitui políticas.
Ingestion recebe apenas conteúdo bruto aprovado.
```
