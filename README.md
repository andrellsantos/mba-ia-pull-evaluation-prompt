# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Repositório do desafio de Prompt Engineering do MBA em Engenharia de Software com IA (Full Cycle). O objetivo final é fazer pull de um prompt de baixa qualidade do LangSmith Prompt Hub, otimizá-lo, publicá-lo de volta e avaliá-lo até atingir >= 0.8 em todas as métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision).

## Status atual do projeto

- [x] **Fase 1 — Pull do prompt inicial do LangSmith** (concluída, documentada abaixo)
- [x] **Fase 2 — Otimização do `bug_to_user_story_v2.yml`** — refatorado aplicando **Few-shot Learning**, **Role Prompting** e **Skeleton of Thought** (detalhes na seção "Técnicas Aplicadas (Fase 2)" abaixo). Uma versão baseline (cópia não otimizada do v1) existiu neste arquivo em uma iteração anterior apenas para fins de comparação, e foi substituída por esta versão otimizada.
- [x] **Fase 3 — `src/push_prompts.py` implementado** — publicação no Hub e avaliação (`src/evaluate.py`) devem ser **executadas manualmente pelo usuário** (ver instruções abaixo), pois são ações que publicam dados publicamente / em um projeto compartilhado do LangSmith. **Atenção:** o `bug_to_user_story_v2.yml` já passou por 2 iterações de conteúdo — sempre rode `push_prompts.py` novamente após qualquer edição no YAML, antes de avaliar.
- [~] **Fase 4 — Iteração em andamento (2 de N):** Iteração 1 reprovou em `correctness` (0.79) e `f1_score` (0.73). Iteração 2 (processo de análise de 5 perguntas + regras de precisão/verbosidade + novos exemplos) corrigiu `correctness` (0.80) mas ainda reprova em `f1_score` (0.76) — falta pouco. Próximo ajuste: reforçar cobertura/recall de informação em relação à `reference` do dataset (ver diagnóstico em "Resultados Finais → Iteração 2").
- [ ] Fase 5 — Testes de validação (`tests/test_prompts.py`)

Este README documenta em detalhes o que já foi implementado/executado e será atualizado conforme as próximas fases forem concluídas.

---

## Pré-requisitos

- **Python 3.9+** (veja a nota sobre Python 3.14 abaixo caso use uma versão muito recente)
- Conta no [LangSmith](https://smith.langchain.com/) com uma API Key
- Conta na [OpenAI](https://platform.openai.com/api-keys) **ou** no [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini, gratuito) para rodar os LLMs

### ⚠️ Nota sobre Python 3.14

As versões fixadas em `requirements.txt` (ex: `pydantic==2.10.4`) não possuem *wheels* pré-compiladas para Python 3.14 e a compilação nativa do `pydantic-core` falha (o toolchain do PyO3 ainda não suporta o ABI do 3.14). Se você estiver em Python 3.14, use um dos caminhos abaixo:

1. **Recomendado:** use Python 3.11/3.12 para o venv (evita qualquer problema de compatibilidade); ou
2. Instale as dependências sem fixar a versão do `pydantic`, deixando o `pip` escolher uma versão compatível com wheel pronta:
   ```bash
   pip install -r <(grep -v '^pydantic==' requirements.txt)
   pip install pydantic
   ```
   (no Windows/PowerShell, remova a linha `pydantic==2.10.4` de uma cópia do `requirements.txt` antes de instalar)

---

## Instalação

Crie e ative um ambiente virtual antes de instalar as dependências:

```bash
python -m venv venv

# Ativar o venv
# Linux/macOS:
source venv/bin/activate
# Windows (cmd):
venv\Scripts\activate.bat
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (Git Bash):
source venv/Scripts/activate

pip install -r requirements.txt
```

## Configuração do `.env`

Copie o template e preencha suas credenciais:

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

Edite o `.env` com:

| Variável | Onde obter |
|---|---|
| `LANGSMITH_API_KEY` | [smith.langchain.com](https://smith.langchain.com/) → Settings → API Keys |
| `LANGSMITH_PROJECT` | Nome do projeto no LangSmith (ex: `mba-ia-pull-evaluation-prompt`) |
| `USERNAME_LANGSMITH_HUB` | Publique qualquer prompt no LangSmith Hub, abra-o e clique no ícone de cadeado (🔒) para ver seu username |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) (se `LLM_PROVIDER=openai`) |
| `GOOGLE_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (se `LLM_PROVIDER=google`) |

O `LANGSMITH_API_KEY` é a única variável obrigatória para a Fase 1 (pull do prompt); as demais são necessárias para as próximas fases (avaliação com LLM).

---

## Fase 1 — Pull do Prompt inicial do LangSmith

### O que foi implementado

O script [`src/pull_prompts.py`](src/pull_prompts.py) foi implementado para:

1. Carregar as credenciais do `.env` (`load_dotenv()`) e validar que `LANGSMITH_API_KEY` está configurada (`check_env_vars`).
2. Conectar ao LangSmith Prompt Hub e fazer `hub.pull("leonanluppi/bug_to_user_story_v1")`, que baixa o `ChatPromptTemplate` publicado no Hub.
3. Percorrer as mensagens do template (`prompt.messages`) e separar o texto de `system_prompt` (mensagem do tipo *system*) e `user_prompt` (mensagem do tipo *human*), com um fallback para templates simples de uma única string.
4. Montar um dicionário com `description`, `system_prompt`, `user_prompt`, `version` e `source` (o identificador do prompt no Hub, para rastreabilidade).
5. Salvar o resultado em `prompts/bug_to_user_story_v1.yml` via `save_yaml` (utilitário já pronto em `src/utils.py`).

Também foi adicionado um ajuste de encoding (`sys.stdout.reconfigure(encoding="utf-8")`) para evitar `UnicodeEncodeError` ao imprimir os emojis (`✅`/`❌`) no console do Windows, cujo codepage padrão (`cp1252`) não suporta esses caracteres.

### Como executar

Com o venv ativado e o `.env` configurado:

```bash
python src/pull_prompts.py
```

### Saída esperada

```
==================================================
Fazendo pull do prompt: leonanluppi/bug_to_user_story_v1
==================================================

✅ Prompt salvo em: <caminho>/prompts/bug_to_user_story_v1.yml
```

O script termina com código de saída `0` em caso de sucesso e `1` caso a `LANGSMITH_API_KEY` não esteja configurada ou o pull falhe (ex: prompt inexistente, credencial inválida, sem conexão).

### Resultado obtido

A execução foi validada de ponta a ponta contra o LangSmith real e gerou o arquivo [`prompts/bug_to_user_story_v1.yml`](prompts/bug_to_user_story_v1.yml) com o conteúdo do prompt publicado em `leonanluppi/bug_to_user_story_v1` — o mesmo prompt de baixa qualidade descrito no enunciado do desafio (sem persona definida, instruções vagas, sem exemplos, sem tratamento de edge cases), que servirá de base para a otimização na Fase 2.

---

## Técnicas Aplicadas (Fase 2)

O prompt [`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml) foi refatorado a partir do v1 (baixa qualidade) aplicando três técnicas de Prompt Engineering:

### 1. Role Prompting

**O que foi feito:** o `system_prompt` abre definindo explicitamente a persona: *"Você é um Senior Product Manager especializado em converter relatos de bugs em User Stories para Produto, QA e Desenvolvimento"*, com uma frase adicional de contexto/experiência.

**Por quê:** o v1 não definia nenhuma persona ("Você é um assistente que ajuda..."), o que deixa o tom e o nível de profundidade da resposta inconsistentes. Atribuir uma persona sênior e específica do domínio (Produto/QA/Dev) ancora o modelo no vocabulário, tom e nível de detalhe técnico corretos, impactando diretamente as métricas de **Clarity** (tom consistente) e **Helpfulness**.

**Exemplo prático (trecho do prompt):**
```
# PERSONA
Você é um Senior Product Manager especializado em converter relatos de bugs em
User Stories para Produto, QA e Desenvolvimento. Você tem anos de experiência
traduzindo relatos confusos e técnicos de usuários e QA em User Stories claras,
acionáveis e prontas para entrar no backlog de um time ágil.
```

### 2. Skeleton of Thought (SoT)

**O que foi feito:** o prompt define um **processo de análise explícito de 5 perguntas** (`PROCESSO DE ANÁLISE`) que o modelo deve responder mentalmente antes de escrever qualquer texto, e um **esqueleto de resposta de 4 seções** (`Título da User Story` → `User Story` → `Critérios de Aceitação` → `Observações Técnicas`) derivado diretamente dessas perguntas.

**Por quê:** na primeira iteração, o Skeleton of Thought já existia, mas apenas como uma lista de seções de saída — sem nenhum passo de análise anterior. Como os resultados da avaliação ainda não atingiram o mínimo de 0.8 em todas as métricas, esta iteração aprofunda a técnica: agora o modelo é forçado a identificar explicitamente *quem* é afetado, *qual ação* falta, *qual benefício* está implícito e *quais fatos concretos* (números, plataformas, endpoints, logs) precisam aparecer, antes de decidir a estrutura final. Isso reduz respostas genéricas e aproxima o conteúdo gerado da referência (`reference`) do dataset, impactando **F1-Score**, **Correctness** e **Clarity**.

**Exemplo prático (trecho do prompt):**
```
# PROCESSO DE ANÁLISE (Skeleton of Thought)
1. Quem é o usuário ou sistema afetado?
2. Qual ação corrigida a pessoa/sistema precisa conseguir?
3. Qual benefício direto aparece no relato?
4. Quais fatos, números, plataformas, endpoints, logs e sintomas devem aparecer?
5. Qual é o menor conjunto de seções necessário para espelhar o bug?
```

### 3. Few-shot Learning (obrigatório)

**O que foi feito:** foram incluídos **3 exemplos completos** de entrada/saída no `system_prompt`: um com **gatilho técnico explícito** (endpoint, status HTTP e log de erro), um **sem nenhum gatilho técnico** (demonstrando a omissão deliberada da seção "Observações Técnicas") e um **edge case de múltiplos problemas** no mesmo relato (demonstrando como focar no problema principal e citar o secundário como observação).

**Por quê:** o v1 não tinha nenhum exemplo — o modelo tinha que "adivinhar" o formato e nível de qualidade esperado. Nesta iteração, os exemplos foram trocados para ensinar, na prática, a regra de verbosidade condicional (seção 4 do esqueleto): o modelo vê lado a lado um caso em que a seção técnica é necessária e um caso em que ela deve ser omitida, o que deveria reduzir texto genérico/desnecessário e subir **Clarity** e **Precision**.

**Exemplo prático (um dos 3 exemplos incluídos no prompt — caso "sem gatilho técnico"):**
```
Relato de Bug: "O botão 'Cancelar Pedido' some da tela quando o pedido está
pendente há mais de 24 horas, mesmo que ele ainda não tenha sido processado."

Resposta esperada:
1. Título da User Story: Botão "Cancelar Pedido" desaparece após 24 horas...
2. User Story: Como um cliente com um pedido pendente há mais de 24 horas...
3. Critérios de Aceitação: (5 bullets Dado que/Quando/Então/E)
(sem seção 4 — relato não traz nenhum gatilho técnico, então a seção é omitida)
```

### 4. Regras de Precisão e Controle de Verbosidade (refinamento da iteração 2)

**O que foi feito:** foi adicionada uma seção `REGRAS DE PRECISÃO E CONTROLE DE VERBOSIDADE` que instrui o modelo a: reutilizar termos/números/endpoints/status citados no relato original (em vez de generalizar), nunca inventar detalhes ausentes, nunca criar seções além das 4 do esqueleto sem gatilho explícito, manter Markdown simples (sem tabelas/emojis/negrito solto), preferir 5 critérios de aceitação para bugs simples, e só incluir a seção "Observações Técnicas" quando o relato trouxer logs, SQL, z-index, performance, segurança, race condition, endpoint/status HTTP específico ou mais de um problema relatado.

**Por quê:** essa não é uma das 3 técnicas "nomeadas" do curso, mas um refinamento necessário para que as técnicas anteriores funcionem bem juntas — sem essas regras, o modelo tende a "inflar" a resposta com seções técnicas genéricas mesmo quando o relato não traz informação técnica nenhuma, o que diverge da referência (`reference`) do dataset e penaliza **Precision** (informação inventada/irrelevante) e **F1-Score** (recall/precision do LLM-judge contra o ground truth).

### Outros requisitos do prompt otimizado (checklist do enunciado)

- **Instruções claras e específicas:** seções `# OBJETIVO`, `# PROCESSO DE ANÁLISE` e `# ESQUELETO DE RESPOSTA`.
- **Regras explícitas de comportamento:** seções `# REGRAS DE PRECISÃO E CONTROLE DE VERBOSIDADE` e `# REGRAS OBRIGATÓRIAS` (idioma, nunca inventar detalhes, nunca copiar o relato literalmente, tom profissional/empático, etc.).
- **Tratamento de edge cases:** regras explícitas para relato vago/incompleto (não inventar detalhes concretos) e relato com múltiplos problemas (focar no principal, citar o(s) demais como observação técnica) + os Exemplos 2 e 3 (few-shot) demonstrando esse comportamento na prática.
- **System vs. User prompt:** o `system_prompt` carrega toda a persona/processo de análise/esqueleto/regras/exemplos (comportamento fixo do agente); o `user_prompt` permanece minimalista (`"{bug_report}"`), carregando apenas o dado variável de cada execução — separação clara entre "como agir" (system) e "sobre o quê agir agora" (user).

---

## Fase 3 — Push e Avaliação

### O que foi implementado

O script [`src/push_prompts.py`](src/push_prompts.py) foi implementado para:

1. Validar `LANGSMITH_API_KEY` no `.env`.
2. Carregar `prompts/bug_to_user_story_v2.yml` (`load_yaml`).
3. Validar a estrutura básica do prompt (`validate_prompt`): campos obrigatórios preenchidos (`description`, `system_prompt`, `user_prompt`, `version`) e ausência de marcações `TODO` pendentes.
4. Montar um `ChatPromptTemplate` (mensagens `system` + `human`) a partir do YAML.
5. Publicar no LangSmith Hub via `hub.push("bug_to_user_story_v2", template, new_repo_is_public=True, ...)` — o prompt é publicado **sob o seu próprio usuário/handle** (a API já usa o dono da API key quando não se informa `owner/` no nome), com `tags` e descrição (incluindo as técnicas aplicadas, se houver) como metadados.
6. Imprimir a URL pública retornada pelo Hub em caso de sucesso.

O código foi revisado e testado com `py_compile` (sem erros de sintaxe/import), mas **a execução real (que publica o prompt publicamente) não foi disparada por mim** — por ser uma ação que expõe dados no seu workspace do LangSmith publicamente, o comando foi deixado para você rodar diretamente, junto com a avaliação (`src/evaluate.py`), que também grava resultados em um projeto compartilhado do LangSmith.

### Como executar (você mesmo, no seu terminal)

Com o venv ativado e o `.env` configurado, **a partir da raiz do projeto**:

```bash
# 1. Publicar o prompt v2 no LangSmith Hub (público)
python src/push_prompts.py
```

Saída esperada em caso de sucesso:

```
==================================================
Fazendo push do prompt: bug_to_user_story_v2
==================================================

✅ Prompt publicado com sucesso: https://smith.langchain.com/prompts/bug_to_user_story_v2/...
```

**Antes de avaliar**, confirme/preencha `USERNAME_LANGSMITH_HUB` no `.env` — é o seu handle público no Hub (aparece na URL retornada pelo push, ou clicando no ícone de cadeado 🔒 do prompt na interface do LangSmith). O `src/evaluate.py` usa essa variável para montar o nome `{username}/bug_to_user_story_v2` e puxar o prompt de volta do Hub antes de avaliar.

> ⚠️ **Nota:** ao inspecionar sua conta via API, o campo `tenant_handle` do workspace ainda estava `None` no momento desta implementação — ou seja, você talvez **ainda não tenha um handle público definido**. Se o `push_prompts.py` falhar com erro relacionado a "handle" ou "owner", acesse [smith.langchain.com](https://smith.langchain.com/), vá em **Settings → Workspace** (ou publique manualmente um prompt de teste pela UI) para definir seu handle público antes de rodar o script novamente.

```bash
# 2. Rodar a avaliação contra o dataset de 15 exemplos
python src/evaluate.py
```

O `evaluate.py` (já pronto, não alterado) irá:
- Criar/reaproveitar o dataset de avaliação no LangSmith a partir de `datasets/bug_to_user_story.jsonl`
- Puxar `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` do Hub
- Rodar o prompt contra os 15 exemplos usando o LLM configurado em `LLM_PROVIDER`/`LLM_MODEL`
- Calcular as 5 métricas e exibir o resultado no terminal, além de publicar os resultados no seu projeto do LangSmith

## Resultados Finais

### Iteração 1 — `bug_to_user_story_v2` (Few-shot + Role Prompting + Skeleton of Thought, sem processo de análise/regras de precisão)

Execução real via `python src/evaluate.py`, provider `openai` (`gpt-4o-mini` para responder, `gpt-4o` para avaliar), contra os 15 exemplos de `datasets/bug_to_user_story.jsonl`:

| Métrica | Score | Threshold | Status |
|---|---|---|---|
| Helpfulness (derivada) | 0.86 | 0.8 | ✅ |
| Correctness (derivada) | 0.79 | 0.8 | ❌ |
| F1-Score | 0.73 | 0.8 | ❌ |
| Clarity | 0.87 | 0.8 | ✅ |
| Precision | 0.84 | 0.8 | ✅ |
| **Média geral** | **0.8183** | 0.8 | — |

**Status: ❌ REPROVADO** — apesar da média geral (0.8183) já superar 0.8, a regra do desafio exige as **5 métricas individualmente** ≥ 0.8, e `correctness` e `f1_score` ficaram abaixo (0.79 e 0.73).

**Diagnóstico:** o F1-Score por exemplo variou bastante (de 0.58 a 0.89 entre os 15 casos), com vários exemplos na faixa 0.58–0.69 — indicando que a resposta gerada, embora clara (Clarity 0.87) e sem muita alucinação (Precision 0.84), ainda diverge estruturalmente/em conteúdo da `reference` do dataset em boa parte dos casos (baixo *recall* de informações esperadas, conforme o critério de F1-Score do avaliador). Foi exatamente esse resultado que motivou a **Iteração 2** (já aplicada em `prompts/bug_to_user_story_v2.yml`, ver seção "Técnicas Aplicadas (Fase 2)"): processo de análise explícito de 5 perguntas, regras de precisão (reaproveitar termos/números/endpoints do relato) e novos exemplos de few-shot — mudanças voltadas justamente a reduzir a divergência resposta-vs-referência que penaliza F1/Correctness.

### Iteração 2 — `bug_to_user_story_v2` (+ Processo de Análise + Regras de Precisão/Verbosidade)

Execução real via `python src/evaluate.py`, mesmo provider/modelos da Iteração 1, contra os mesmos 15 exemplos:

| Métrica | Iteração 1 | Iteração 2 | Threshold | Status |
|---|---|---|---|---|
| Helpfulness (derivada) | 0.86 | 0.86 | 0.8 | ✅ |
| Correctness (derivada) | 0.79 | 0.80 | 0.8 | ✅ |
| F1-Score | 0.73 | 0.76 | 0.8 | ❌ |
| Clarity | 0.87 | 0.88 | 0.8 | ✅ |
| Precision | 0.84 | 0.85 | 0.8 | ✅ |
| **Média geral** | 0.8183 | **0.8285** | 0.8 | — |

**Status: ❌ REPROVADO** — todas as métricas subiram em relação à Iteração 1, e `correctness` passou a ficar ≥ 0.8. Falta apenas **F1-Score** (0.76), agora a única métrica abaixo do threshold — e a mais próxima de passar até agora.

**Diagnóstico:** olhando os 15 scores individuais de F1, os piores casos ficaram em 0.55–0.69 (exemplos 2, 5, 9, 1, 10, 4), enquanto os melhores chegaram a 0.90–1.00 (exemplos 7, 13, 14, 15). Como Precision (métrica isolada) já está alta (0.85) e Clarity também (0.88), a divergência não é por alucinação nem por falta de organização — o F1-Score do avaliador combina *precision* e *recall* específicos da resposta contra a referência, então o gargalo provável é **recall**: em parte dos 15 exemplos a resposta ainda deixa de cobrir algum detalhe/comportamento presente na `reference` do dataset (ex: um critério de aceitação a mais que a referência tem e a resposta não cobriu, ou uma nuance do relato original não refletida). Isso aponta para a Iteração 3: reforçar no prompt a cobertura completa dos comportamentos/condições citados no relato (sem se limitar a "5 critérios" quando o relato sugerir mais de 5 condições relevantes) antes de fechar a resposta.

### Iteração 3 — pendente

*(Aguardando ajuste do prompt focado em F1-Score/recall, novo `push_prompts.py` + `evaluate.py`, e a saída correspondente.)*

### Link do dashboard e screenshots

*(Pendente: adicionar aqui o link público do projeto no LangSmith — `https://smith.langchain.com/projects/mba-ia-pull-evaluation-prompt` — e screenshots das avaliações/tracing, conforme exigido no critério "Entregável" do desafio.)*

---

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example              # Template das variáveis de ambiente
├── requirements.txt          # Dependências Python
├── README.md                 # Este arquivo
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial (pull do LangSmith Hub) ✅
│   └── bug_to_user_story_v2.yml  # Otimizado: Few-shot + Role Prompting + Skeleton of Thought (Fase 2) ✅
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs para avaliação
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith ✅ implementado
│   ├── push_prompts.py       # Push ao LangSmith ✅ implementado (execução manual pendente)
│   ├── evaluate.py           # Avaliação automática (pronto, não alterar)
│   ├── metrics.py            # 5 métricas implementadas (pronto, não alterar)
│   └── utils.py              # Funções auxiliares (pronto, não alterar)
│
└── tests/
    └── test_prompts.py       # Testes de validação (Fase 5, pendente)
```

## Próximos passos

- **Pendente (você):** rodar `python src/push_prompts.py` e depois `python src/evaluate.py` sobre a Iteração 2 do prompt (veja "Resultados Finais → Iteração 2" acima) e compartilhar a saída.
- **Fase 4 (iteração):** a Iteração 1 reprovou em `correctness` (0.79) e `f1_score` (0.73) — ver diagnóstico em "Resultados Finais". Se a Iteração 2 ainda não atingir 0.8 em todas as métricas, seguimos analisando o `reasoning` de cada métrica e ajustando o prompt (espera-se 3-5 iterações no total).
- **Fase 5:** implementar os 6 testes em `tests/test_prompts.py` e validar com `pytest tests/test_prompts.py`.
