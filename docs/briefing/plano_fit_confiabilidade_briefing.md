# Plano de melhoria de fit, confiabilidade e briefing

## Objetivo

Melhorar a qualidade das recomendacoes NVIDIA e do briefing executivo para que o sistema deixe de parecer uma busca por palavras-chave e passe a operar como uma analise baseada em evidencias, incertezas explicitas e criterios de fit.

O problema observado no caso Kunumi foi claro: o pipeline conseguiu coletar fontes e gerar recomendacoes, mas o resultado ainda ficou fraco. Algumas recomendacoes apareceram com baixo fit, baixa confianca ou justificativas genericas. O briefing tambem explicou pouco o motivo da recomendacao e nao separava bem uma indicacao forte de uma hipotese exploratoria.

## Como o briefing funciona atualmente

O briefing e gerado pelo caso de uso `GenerateBriefing`, no modulo `apps/api/src/modules/briefing`.

Fluxo atual:

1. O sistema busca o perfil da startup.
2. Busca as recomendacoes NVIDIA ja geradas para essa startup.
3. Busca as evidencias coletadas no processo de ingestao.
4. Opcionalmente consulta o contexto NVIDIA via RAG, usando as recomendacoes como entrada.
5. Monta um markdown com resumo, evidencias, recomendacoes, contexto NVIDIA, riscos e proximas acoes.
6. Substitui o briefing anterior da startup pelo novo briefing.

As recomendacoes usadas pelo briefing vem do modulo `apps/api/src/modules/recommendations`.

Fluxo atual de recomendacao:

1. O sistema transforma evidencias da startup em sinais de texto.
2. O catalogo NVIDIA fornece candidatos de tecnologia, cada um com nome, categoria, palavras-chave, casos de uso e complexidade.
3. A politica `match_technologies` compara palavras-chave do catalogo com setor, descricao, tags e evidencias da startup.
4. O score de fit e calculado principalmente pela proporcao de palavras-chave encontradas.
5. A confianca vem da qualidade das evidencias encontradas; quando o match vem apenas do perfil, a confianca e limitada.
6. Para recomendacoes aceitas, o sistema tenta enriquecer a justificativa com contexto RAG da base NVIDIA.
7. As recomendacoes anteriores sao substituidas pelas novas.

Melhoria ja aplicada:

- O motor passou a exigir pelo menos dois sinais de match para recomendar uma tecnologia.
- Matches com uma unica palavra generica, como `platform`, deixam de ser suficientes.
- O briefing agora recebe `confidence` e `complexity` das recomendacoes.
- O briefing passou a incluir uma leitura executiva indicando se a recomendacao e forte, moderada ou exploratoria.
- Quando o fit ou a confianca sao baixos, a proxima acao passa a ser validar o workload real de IA/GPU antes de propor implementacao.

## Fraquezas atuais

### 1. Fit ainda depende demais de palavras-chave

O algoritmo atual mede fit principalmente por sobreposicao de termos. Isso e simples e previsivel, mas pode gerar falsos positivos quando uma palavra aparece sem contexto suficiente.

Exemplo: uma fonte mencionar "platform" nao significa que a startup precise de NVIDIA AI Enterprise.

### 2. A confianca mede a fonte, nao necessariamente o encaixe

Hoje a confianca vem muito da qualidade da evidencia coletada. Uma fonte pode ser confiavel, mas ainda assim nao provar que a recomendacao e boa.

Confianca deveria combinar:

- qualidade da fonte;
- clareza do sinal encontrado;
- proximidade entre problema da startup e tecnologia NVIDIA;
- quantidade de evidencias independentes;
- existencia de dados operacionais concretos.

### 3. Falta um perfil estruturado de workload

O sistema ainda nao extrai de forma robusta perguntas centrais:

- A startup treina modelos ou apenas usa IA via API?
- Existe inferencia em producao?
- Ha necessidade real de GPU?
- O workload e NLP, visao computacional, recomendacao, simulacao, analytics ou MLOps?
- Qual escala, latencia, volume de dados e maturidade tecnica?
- A empresa esta em pesquisa, MVP, piloto, producao ou escala?
- Qual ambiente atual: cloud, on-premise, edge ou hibrido?

Sem isso, o briefing consegue falar sobre tecnologias NVIDIA, mas nao consegue provar com forca que a startup precisa delas.

### 4. RAG ainda fundamenta a tecnologia, nao o fit

O RAG ajuda a explicar o que uma tecnologia NVIDIA faz. Ele ainda nao valida se aquela tecnologia e adequada para a startup.

Ou seja: ele melhora a descricao da solucao, mas nao resolve sozinho a pergunta mais importante: "por que esta startup precisa disso agora?"

### 5. Recomendacoes exploratorias aparecem perto demais de recomendacoes fortes

Antes da melhoria recente, uma recomendacao de baixo fit podia aparecer como se fosse uma recomendacao normal. Agora o briefing ja marca recomendacoes exploratorias, mas a interface e o modelo de dados ainda precisam reforcar melhor essa separacao.

### 6. Falta avaliacao objetiva

Ainda nao existe um conjunto de startups de referencia com recomendacoes esperadas. Sem esse conjunto, fica dificil saber se cada ajuste melhora precisao ou apenas muda o estilo da resposta.

## Plano de melhoria

### Fase 1: Tornar o fit mais criterioso

Objetivo: reduzir falsos positivos rapidamente.

Implementacoes recomendadas:

- Trocar score simples por um score composto.
- Separar sinais fortes, medios e fracos.
- Penalizar termos genericos como `platform`, `data`, `AI`, `machine learning`, `cloud` quando aparecem sozinhos.
- Exigir evidencia concreta para recomendacoes tecnicas.
- Permitir recomendacoes programaticas, como NVIDIA Inception, com uma regra propria.
- Guardar no resultado quais sinais sustentaram cada recomendacao.

Rubrica sugerida de fit:

- alinhamento de workload: 35%;
- evidencia concreta encontrada: 25%;
- maturidade da startup: 15%;
- valor NVIDIA especifico: 15%;
- viabilidade de implementacao: 10%.

### Fase 2: Extrair um perfil estruturado da startup

Objetivo: transformar texto coletado em campos que o motor consiga comparar com o catalogo NVIDIA.

Novo artefato sugerido: `StartupAIProfile`.

Campos sugeridos:

- `ai_workload_type`;
- `model_type`;
- `data_modality`;
- `deployment_stage`;
- `infra_environment`;
- `gpu_need`;
- `latency_requirement`;
- `scale_signal`;
- `current_tools`;
- `business_goal`;
- `evidence_ids`;
- `field_confidence`.

Esse perfil deve ser montado a partir das evidencias coletadas e deve guardar a origem de cada campo.

### Fase 3: Reescrever a recomendacao como matriz de decisao

Objetivo: cada tecnologia NVIDIA deve ter criterios claros de entrada.

Exemplo:

- NVIDIA Inception:
  - startup ativa;
  - sinal de uso ou construcao de IA;
  - potencial de beneficio em credito, networking, go-to-market ou suporte.

- cuML:
  - workload de machine learning classico;
  - datasets tabulares ou analytics;
  - gargalo de treino/inferencia em CPU;
  - maturidade tecnica suficiente para adotar RAPIDS.

- NVIDIA AI Enterprise:
  - IA corporativa em producao;
  - necessidade de governanca, suporte, padronizacao e operacao;
  - ambiente enterprise ou regulated.

Saida esperada por recomendacao:

- fit score;
- confidence score;
- nivel: forte, moderada, exploratoria ou sem fit;
- sinais usados;
- evidencias usadas;
- informacoes faltantes;
- motivo de rejeicao quando nao recomendar.

### Fase 4: Melhorar o briefing

Objetivo: o briefing deve ser mais util para decisao humana, nao apenas uma lista de recomendacoes.

Nova estrutura recomendada:

1. Resumo executivo.
2. Tese de fit NVIDIA.
3. Nivel de confianca geral.
4. O que foi encontrado.
5. O que nao foi encontrado.
6. Matriz de recomendacoes.
7. Recomendacoes fortes.
8. Hipoteses exploratorias.
9. Perguntas de qualificacao.
10. Proximas acoes sugeridas.

O briefing deve sempre deixar claro:

- se a recomendacao e acionavel agora;
- se e apenas uma hipotese;
- quais evidencias sustentam a conclusao;
- quais informacoes faltam;
- qual pergunta deve ser feita ao fundador ou ao time tecnico.

### Fase 5: Criar avaliacao com casos conhecidos

Objetivo: medir se o sistema esta melhorando de verdade.

Criar uma base pequena de validacao com startups conhecidas e expectativas manuais:

- startup com IA forte e necessidade de GPU;
- startup que usa IA apenas superficialmente;
- startup de SaaS sem workload NVIDIA claro;
- startup de visao computacional;
- startup de analytics tabular;
- startup enterprise com MLOps/governanca.

Metricas sugeridas:

- precision@3 das recomendacoes;
- taxa de falsos positivos;
- taxa de recomendacoes exploratorias corretamente marcadas;
- percentual de recomendacoes com evidencias rastreaveis;
- avaliacao humana da justificativa.

### Fase 6: Robustez operacional

Objetivo: tornar a geracao auditavel e recuperavel.

Melhorias recomendadas:

- versionar briefing e recomendacoes, em vez de apenas substituir;
- registrar modelo, prompts, fontes, custos e tempo de execucao;
- permitir reprocessamento por etapa;
- expor no frontend o motivo de baixa confianca;
- separar erro tecnico de resultado inconclusivo;
- manter historico de aprovacoes/rejeicoes para calibrar o motor.

## Criterios de aceite

O briefing deve ser considerado mais robusto quando:

- uma startup com evidencias fracas nao gerar varias recomendacoes tecnicas rasas;
- toda recomendacao tecnica tiver pelo menos dois sinais relevantes ou uma regra explicita;
- toda recomendacao mostrar evidencias ou declarar que faltam evidencias;
- recomendacoes de baixa confianca forem marcadas como exploratorias;
- o usuario conseguir entender por que a tecnologia foi recomendada;
- o sistema sugerir perguntas objetivas quando nao houver informacao suficiente;
- testes unitarios cobrirem falso positivo por palavra generica;
- existir uma suite de avaliacao com startups de referencia.

## Ordem pratica de implementacao

1. Adicionar um breakdown de fit nas recomendacoes.
2. Criar o `StartupAIProfile` estruturado.
3. Trocar o match por palavra-chave simples por scoring ponderado.
4. Atualizar o briefing para exibir matriz de fit, confianca e informacoes faltantes.
5. Criar dataset de avaliacao com casos conhecidos.
6. Ajustar frontend para separar recomendacoes fortes de hipoteses exploratorias.

## Estado atual apos a primeira melhoria

No caso Kunumi, o sistema passou a reduzir recomendacoes rasas. Antes apareciam varias tecnologias com baixo fit. Depois da primeira melhoria, a recomendacao ficou concentrada em NVIDIA Inception, com leitura exploratoria, fit baixo/moderado e confianca explicita.

Isso e um bom primeiro passo porque evita excesso de recomendacoes fracas. O proximo salto de qualidade vem de extrair um perfil estruturado da startup e usar esse perfil para justificar o fit de forma mais profunda.
