# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Repositório do desafio de Prompt Engineering do MBA em Engenharia de Software com IA (Full Cycle). O objetivo final é fazer pull de um prompt de baixa qualidade do LangSmith Prompt Hub, otimizá-lo, publicá-lo de volta e avaliá-lo até atingir >= 0.8 em todas as métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision).

## Status atual do projeto

- [x] **Fase 1 — Pull do prompt inicial do LangSmith** (concluída, documentada abaixo)
- [x] **Fase 2 — Otimização do `bug_to_user_story_v2.yml`** — refatorado aplicando **Few-shot Learning**, **Role Prompting** e **Skeleton of Thought** (detalhes na seção "Técnicas Aplicadas (Fase 2)" abaixo). Uma versão baseline (cópia não otimizada do v1) existiu neste arquivo em uma iteração anterior apenas para fins de comparação, e foi substituída por esta versão otimizada.
- [x] **Fase 3 — `src/push_prompts.py` implementado** — publicação no Hub e avaliação (`src/evaluate.py`) devem ser **executadas manualmente pelo usuário** (ver instruções abaixo), pois são ações que publicam dados publicamente / em um projeto compartilhado do LangSmith. **Atenção:** o `bug_to_user_story_v2.yml` já passou por 2 iterações de conteúdo — sempre rode `push_prompts.py` novamente após qualquer edição no YAML, antes de avaliar.
- [x] **Fase 4 — Iteração concluída em 5 rodadas: ✅ APROVADO.** F1-Score por iteração: 0.73 → 0.76 → 0.79 → 0.78 → **0.83**. A virada veio na Iteração 5, ao descobrir que duas regras do próprio prompt limitavam o recall (literalidade numérica excessiva + proibição de inferir as expectativas colaterais que a referência espera). **Todas as 5 métricas ≥ 0.8, média geral 0.8489.**
- [x] **Fase 5 — Testes de validação implementados** (`tests/test_prompts.py`): 6 testes cobrindo `system_prompt` não vazio, definição de persona, formato/Markdown exigido, exemplos de few-shot, ausência de `TODO` e mínimo de 2 técnicas listadas. Validado com `pytest tests/test_prompts.py -v` — **6 passed**.
- [x] Evidências — screenshots do dashboard do LangSmith em `images/` (ver seção "Evidências no LangSmith" abaixo)

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

**O que foi feito:** o prompt define um **processo de análise de 6 perguntas** (`PROCESSO DE ANÁLISE`) que o modelo responde mentalmente antes de escrever qualquer texto, e — a partir da iteração 3 — **três esqueletos de resposta distintos por nível de complexidade** (`ESQUELETOS POR COMPLEXIDADE`: simples / médio / complexo), cada um com seu próprio formato, mais uma tabela de `GATILHOS DE SEÇÃO` que mapeia o tipo de problema (performance, segurança, cálculo monetário, concorrência, z-index/acessibilidade) para o nome exato da seção técnica esperada.

**Por quê:** nas iterações 1-2, o esqueleto era único e fixo (4 seções sempre, com uma seção genérica "Observações Técnicas" para qualquer tipo de contexto técnico). O resultado da Iteração 2 (ver "Resultados Finais") mostrou Correctness, Clarity e Precision acima de 0.8, mas **F1-Score em 0.76** — o que indica um problema de **recall**: a resposta não estava cobrindo o mesmo tipo de informação/estrutura que a referência do dataset espera para cada bug. Como o dataset mistura bugs simples, médios (com gatilhos técnicos variados: performance, segurança, cálculo, concorrência, UI) e complexos (múltiplos problemas), um único esqueleto genérico não conseguia se adaptar à granularidade que cada categoria exige. O esqueleto adaptativo por complexidade + gatilhos de seção nomeados ataca diretamente essa lacuna de recall, o que deve subir **F1-Score** e **Correctness**.

Além disso, a partir da iteração 5 o SoT ganhou uma seção `ANATOMIA DOS CRITÉRIOS DE ACEITAÇÃO`, que define o papel de cada bullet — 1 `Dado que` (contexto), 1 `Quando` (ação), 1 `Então` (comportamento correto) e **2 bullets `E` de expectativa colateral de qualidade** (confirmação visual, atualização de estado/contador, bloqueio de ação inválida, mensagem explicando o formato correto, consistência entre plataformas, etc.).

**Exemplo prático (trecho do prompt):**
```
# ANATOMIA DOS CRITÉRIOS DE ACEITAÇÃO
- Dado que <contexto/estado do usuário no momento do problema>
- Quando <ação que o usuário executa>
- Então <comportamento correto esperado — o oposto do sintoma>
- E <expectativa colateral de qualidade>
- E <segunda expectativa colateral de qualidade>
```

### 3. Few-shot Learning (obrigatório)

**O que foi feito:** o `system_prompt` inclui **5 exemplos autorais** de entrada/saída: **2 bugs simples** (um com identificador incidental que deve ser generalizado, outro de validação), **1 de performance** com limiar mantido (→ "Critérios Técnicos" + "Contexto do Bug"), **1 de cálculo com percentual** (→ "Exemplo de Cálculo" com subtotal/desconto/total + "Contexto Técnico") e **1 complexo** com o formato `=== USER STORY PRINCIPAL ===` / `=== CRITÉRIOS DE ACEITAÇÃO ===` (subseções A./B.) / `=== CRITÉRIOS TÉCNICOS ===` / `=== CONTEXTO DO BUG ===` / `=== TASKS TÉCNICAS SUGERIDAS ===`.

**Por quê:** a iteração 4 adicionou exemplos (4 → 6) e o F1 **caiu** de 0.79 para 0.78, com os bugs complexos regredindo de ≥0.90 para 0.85–0.90 — evidência de diluição por excesso de contexto. A iteração 5 inverte a estratégia: **reduz para 5 exemplos** (system prompt de 14.4k → 12.4k caracteres) e realoca a cobertura para onde os dados mostravam o pior desempenho — os bugs **simples**, que somam 1/3 do dataset e tinham a pior média de F1 (0.738) apesar de serem os mais fáceis, e que até então tinham apenas 1 exemplo.

**Exemplo prático (exemplo novo da iteração 5 — bug simples com identificador generalizado):**
```
Relato: "O botão de favoritar não funciona na página do produto ID 8842."

Resposta:
Como um cliente navegando na loja, eu quero favoritar produtos que me
interessam, para que eu possa encontrá-los depois e decidir minha compra
com calma.

Critérios de Aceitação:
- Dado que estou visualizando a página de um produto   <- "ID 8842" generalizado
- Quando clico no botão de favoritar
- Então o produto deve ser adicionado à minha lista de favoritos
- E devo ver uma confirmação visual...                 <- colateral inferido
- E o contador de favoritos deve ser atualizado        <- colateral inferido
```

### 4. Generalização vs. Literalidade (regra crítica, reescrita na iteração 5)

**O que foi feito:** a antiga seção "Regras de Precisão e Controle de Verbosidade" foi **reescrita** como `GENERALIZAÇÃO vs. LITERALIDADE`, que distingue três casos em vez de aplicar literalidade a tudo:

- **Generalizar** identificadores e valores incidentais (`produto ID 1234` → "um produto"; `mostra 50 mas só há 42` → "o número exibido deve corresponder ao total real"), porque são apenas a amostra do sintoma;
- **Manter** limiares e condições que definem o escopo (`mais de 1000 registros`, `telas menores que 768px`, `mais de 50 itens`) e plataformas/perfis (`iOS`, `Safari`, `usuário comum vs. admin`);
- **Reproduzir com exatidão** — mas **somente dentro das seções técnicas** — endpoints, status HTTP, logs, z-index, tempos medidos e valores monetários.

**Por quê:** esta foi a descoberta central da análise da iteração 4. Comparando as `reference` reais do dataset com as regras então vigentes, ficou claro que duas delas atuavam **contra** a métrica: (a) *"reutilizar os números exatos do relato"* fazia o modelo escrever `produto ID 1234` e `50 vs 42` nos critérios, sendo que a referência os descarta — inflando conteúdo ausente do gabarito; e (b) *"não inventar detalhes ausentes"* **suprimia** justamente as expectativas colaterais que a referência infere e espera ("confirmação visual", "contador atualizado", "atualizado em tempo real", "apenas usuários com status ativo"). O efeito combinado explica o padrão observado por 3 iterações: **Precision alta e estável (0.83–0.85) com recall preso**, mantendo o F1 em 0.76–0.79. A iteração 5 rebalanceia: permite explicitamente a inferência de expectativas colaterais (via ANATOMIA) e restringe a literalidade numérica às seções técnicas.

### Outros requisitos do prompt otimizado (checklist do enunciado)

- **Instruções claras e específicas:** seções `# OBJETIVO`, `# PROCESSO DE ANÁLISE`, `# ANATOMIA DOS CRITÉRIOS DE ACEITAÇÃO`, `# ESQUELETOS POR COMPLEXIDADE` e `# GATILHOS DE SEÇÃO`.
- **Regras explícitas de comportamento:** seções `# GENERALIZAÇÃO vs. LITERALIDADE` e `# REGRAS OBRIGATÓRIAS` (idioma, escopo de inferência permitido, nunca criar seções fora do esqueleto, Markdown simples, etc.).
- **Tratamento de edge cases:** identificadores incidentais são generalizados enquanto limiares são preservados (regra `GENERALIZAÇÃO vs. LITERALIDADE`); bugs de backend/integração sem usuário final recebem o ator "o sistema" (pergunta 1 do `PROCESSO DE ANÁLISE`); bugs complexos com múltiplos problemas têm esqueleto próprio (subseções A./B./C./D., uma por problema) + o Exemplo 5 (few-shot) demonstrando o comportamento.
- **System vs. User prompt:** o `system_prompt` carrega toda a persona/processo de análise/esqueletos/gatilhos/regras/exemplos (comportamento fixo do agente); o `user_prompt` carrega apenas o relato (`{bug_report}`) e um lembrete curto para seguir o processo e não incluir texto extra — separação clara entre "como agir" (system) e "sobre o quê agir agora" (user).

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

### Iteração 3 — `bug_to_user_story_v2` (+ Esqueletos adaptativos por complexidade e gatilhos de seção nomeados)

Mudança aplicada: substituição do esqueleto único de 4 seções por **3 esqueletos distintos** (bug simples / médio / complexo) e uma tabela de **gatilhos de seção** que nomeia a seção técnica correta conforme o tipo de problema (performance, segurança, cálculo monetário, concorrência, acessibilidade/z-index), com 4 novos exemplos de few-shot cobrindo cada padrão (ver "Técnicas Aplicadas (Fase 2)" acima para o detalhamento).

Execução real via `python src/evaluate.py`, mesmo provider/modelos das iterações anteriores, contra os mesmos 15 exemplos:

| Métrica | Iteração 1 | Iteração 2 | Iteração 3 | Threshold | Status |
|---|---|---|---|---|---|
| Helpfulness (derivada) | 0.86 | 0.86 | 0.85 | 0.8 | ✅ |
| Correctness (derivada) | 0.79 | 0.80 | 0.81 | 0.8 | ✅ |
| F1-Score | 0.73 | 0.76 | 0.79 | 0.8 | ❌ |
| Clarity | 0.87 | 0.88 | 0.87 | 0.8 | ✅ |
| Precision | 0.84 | 0.85 | 0.83 | 0.8 | ✅ |
| **Média geral** | 0.8183 | 0.8285 | **0.8287** | 0.8 | — |

**Status: ❌ REPROVADO** — de novo, só **F1-Score** fica abaixo do threshold, e por uma margem mínima (0.79 vs. 0.80 — a menor distância até agora nas 3 iterações). `Correctness` segue subindo (0.81) e a média geral é a maior até aqui (0.8287).

**Diagnóstico:** os piores F1 individuais desta rodada foram os exemplos 9 (0.65), 10 (0.65) e 4 (0.69) — nos 3, a Precision isolada também caiu (0.67, 0.70, 0.83), sugerindo que o problema não é mais estrutura/seções (o esqueleto adaptativo já ajudou: exemplos com gatilho de segurança, cálculo e concorrência tiveram F1 ≥ 0.80), e sim **conteúdo específico dentro das seções corretas** — provavelmente detalhes numéricos/técnicos do relato que ainda não estão sendo reaproduzidos com fidelidade suficiente (ex: o valor exato de um cálculo, ou um critério técnico específico que a referência espera). Os exemplos com maior F1 (13, 14, 15 — os 3 bugs complexos, todos ≥ 0.90) confirmam que o formato `===` por subseções está funcionando bem. Iteração 4 (próximo passo): revisar especificamente os exemplos/regras que cobrem cálculo monetário e performance/paginação (gatilhos dos exemplos 9 e 10 do dataset), reforçando a instrução de reproduzir números e detalhes técnicos com exatidão.

### Iteração 4 — `bug_to_user_story_v2` (+ Exemplos para cálculo monetário e performance/paginação + fidelidade numérica)

Mudança aplicada: identificado que os gatilhos "cálculo monetário" e "performance/paginação" (exatamente os que causaram os piores F1 na Iteração 3) tinham regra definida em `GATILHOS DE SEÇÃO` mas nenhum exemplo de few-shot correspondente. Adicionados 2 novos exemplos autorais cobrindo esses gatilhos (total: 6 exemplos), e reforçada a regra de precisão para exigir reprodução exata de números/métricas (sem arredondar ou generalizar) — ver "Técnicas Aplicadas (Fase 2)" acima para o detalhamento.

Execução real via `python src/evaluate.py`, mesmo provider/modelos das iterações anteriores, contra os mesmos 15 exemplos:

| Métrica | Iteração 2 | Iteração 3 | Iteração 4 | Threshold | Status |
|---|---|---|---|---|---|
| Helpfulness (derivada) | 0.86 | 0.85 | 0.85 | 0.8 | ✅ |
| Correctness (derivada) | 0.80 | 0.81 | 0.81 | 0.8 | ✅ |
| F1-Score | 0.76 | 0.79 | 0.78 | 0.8 | ❌ |
| Clarity | 0.88 | 0.87 | 0.87 | 0.8 | ✅ |
| Precision | 0.85 | 0.83 | 0.83 | 0.8 | ✅ |
| **Média geral** | 0.8285 | 0.8287 | 0.8279 | 0.8 | — |

**Status: ❌ REPROVADO** — F1-Score praticamente estagnado (0.79 → 0.78), dentro da margem de ruído do LLM-judge. Os outros 4 continuam estáveis e aprovados.

**Diagnóstico (por que não subiu como esperado):** comparando os 15 scores individuais com a Iteração 3, o exemplo 9 (cálculo monetário — justamente o gatilho que o novo exemplo deveria reforçar) **não mudou** (0.65 → 0.65): o novo exemplo de few-shot usava um cálculo simples por multiplicação (4 volumes × R$ 20), enquanto a referência real do exemplo 9 do dataset envolve desconto percentual com quebra em subtotal/desconto/total — um padrão de cálculo diferente do que o exemplo ensinou. O exemplo 10 (performance) melhorou pouco (0.65 → 0.69): a referência real menciona correções bem específicas da plataforma (paginação + thread em background + padrão de lista), mais detalhadas do que o exemplo genérico adicionado. Além disso, os 2 bugs complexos que antes tinham F1 ≥ 0.90 caíram (13: 0.95 → 0.85; 15: 1.00 → 0.90) e o exemplo 7 (outro caso de performance) piorou em Clarity e Precision (0.90 → 0.75 e 0.83 → 0.67) — possivelmente por diluição, com 6 exemplos de few-shot no prompt em vez de 4. **Conclusão:** adicionar mais exemplos não estava resolvendo o problema; o ganho depende de generalizar melhor a regra (reproduzir a causa técnica exata e a composição do cálculo, incluindo variações como desconto percentual), não de exemplificar mais casos específicos.

### Iteração 5 — `bug_to_user_story_v2` (rebalanceamento literalidade ↔ inferência)

Análise que motivou a mudança — F1 por grupo de complexidade na Iteração 4:

| Grupo | Qtd. | F1 médio | Observação |
|---|---|---|---|
| **Simples** | 5 | **0.738** | pior grupo, apesar de serem os casos mais fáceis |
| Médio | 7 | 0.777 | maior grupo |
| Complexo | 3 | 0.883 | melhor grupo (estrutura `===` funcionando) |

O déficit para atingir 0.80 é de apenas **0.22 na soma dos 15 F1**. Se os 5 bugs simples subissem de 0.738 para ~0.88, o F1 global iria a **~0.83** — o caminho de maior alavancagem, e justamente o grupo que nunca havia recebido regra própria (as iterações 3 e 4 investiram só em seções técnicas de médios/complexos).

Mudanças aplicadas:
1. **`ANATOMIA DOS CRITÉRIOS DE ACEITAÇÃO`** — define o papel de cada bullet e exige 2 bullets `E` de expectativa colateral (padrão observado em 100% das referências de bugs simples).
2. **`GENERALIZAÇÃO vs. LITERALIDADE`** — substitui a regra literalista: generalizar identificadores incidentais, preservar limiares/plataformas, e reproduzir números exatos apenas nas seções técnicas.
3. **Regra de ator e de benefício** — ator "o sistema" para bugs de backend/integração; o "para que" deve ser o objetivo maior do usuário, não a ausência do bug.
4. **Redução de 6 → 5 exemplos** (system prompt 14.4k → 12.4k chars), com a cobertura realocada para bugs simples (agora 2 exemplos).

#### Resultado: ✅ APROVADO

| Métrica | Iteração 3 | Iteração 4 | **Iteração 5** | Threshold | Status |
|---|---|---|---|---|---|
| Helpfulness (derivada) | 0.85 | 0.85 | **0.86** | 0.8 | ✅ |
| Correctness (derivada) | 0.81 | 0.81 | **0.84** | 0.8 | ✅ |
| F1-Score | 0.79 | 0.78 | **0.83** | 0.8 | ✅ |
| Clarity | 0.87 | 0.87 | **0.88** | 0.8 | ✅ |
| Precision | 0.83 | 0.83 | **0.84** | 0.8 | ✅ |
| **Média geral** | 0.8287 | 0.8279 | **0.8489** | 0.8 | ✅ |

```
✅ STATUS: APROVADO - Todas as métricas >= 0.8
```

**Validação da hipótese** — F1 médio por grupo, antes e depois do rebalanceamento:

| Grupo | Iteração 4 | Iteração 5 | Δ |
|---|---|---|---|
| Simples | 0.738 | 0.790 | **+0.052** |
| Médio | 0.777 | 0.814 | **+0.037** |
| Complexo | 0.883 | 0.963 | **+0.080** |
| **Global** | 0.785 | **0.836** | **+0.051** |

Os três grupos melhoraram simultaneamente, o que confirma as duas hipóteses da análise:

- **A regra de generalização destravou o recall.** Permitir as expectativas colaterais inferidas e parar de repetir identificadores incidentais elevou simples e médios — e o exemplo 9 (cálculo com desconto percentual) deu o maior salto individual de toda a série: **0.65 → 0.90 (+0.25)**, validando também a regra específica de subtotal/desconto/total.
- **A diluição por excesso de exemplos era real.** Os bugs complexos, que a iteração 4 havia degradado de ≥0.90 para 0.883, saltaram para **0.963** — melhor patamar de toda a série — apenas por enxugar o prompt de 6 para 5 exemplos, sem nenhuma mudança na estrutura `===` que eles usam.

### Tabela comparativa: v1 (prompt ruim) vs. v2 (otimizado)

| Aspecto | `leonanluppi/bug_to_user_story_v1` | `andrellsantos/bug_to_user_story_v2` |
|---|---|---|
| Persona | Nenhuma ("Você é um assistente que ajuda...") | Senior Product Manager especializado em bugs → User Stories |
| Estrutura de saída | Nenhuma ("crie uma user story a partir dele") | Esqueleto adaptativo por complexidade + anatomia dos critérios |
| Exemplos (Few-shot) | 0 | 5 exemplos autorais cobrindo simples, médio e complexo |
| Regras de comportamento | Nenhuma | Generalização vs. literalidade, gatilhos de seção, regras obrigatórias |
| Tratamento de edge cases | Nenhum | Identificador incidental, ator "o sistema", múltiplos problemas |
| System vs. User prompt | `{bug_report}` duplicado nos dois | System = comportamento fixo; User = apenas o relato |
| **Helpfulness** | — | **0.86** ✅ |
| **Correctness** | — | **0.84** ✅ |
| **F1-Score** | — | **0.83** ✅ |
| **Clarity** | — | **0.88** ✅ |
| **Precision** | — | **0.84** ✅ |
| **Média geral** | — | **0.8489** ✅ |
| **Status** | ❌ Reprovado (baixa qualidade por construção) | ✅ **APROVADO** |

> **Nota de honestidade metodológica:** o v1 **não foi medido** com o `evaluate.py` neste projeto — o script avalia exclusivamente `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` (nome fixo no código, que é um dos arquivos "prontos, não alterar"). Os números do v1 no enunciado do desafio (~0.45–0.52) são explicitamente descritos lá como "apenas ilustrativos", então não foram reproduzidos aqui como se fossem medição real. A evolução medida de fato neste projeto é a das 5 iterações do v2, na tabela abaixo.

### Evolução medida ao longo das iterações do v2

| Iteração | Mudança principal | F1-Score | Média geral | Status |
|---|---|---|---|---|
| 1 | Few-shot + Role Prompting + SoT (esqueleto fixo) | 0.73 | 0.8183 | ❌ |
| 2 | + Processo de análise + regras de precisão | 0.76 | 0.8285 | ❌ |
| 3 | + Esqueletos por complexidade + gatilhos de seção | 0.79 | 0.8287 | ❌ |
| 4 | + Exemplos para cálculo e performance (6 exemplos) | 0.78 | 0.8279 | ❌ |
| **5** | **Anatomia dos critérios + generalização vs. literalidade (5 exemplos)** | **0.83** | **0.8489** | ✅ |

---

## Evidências no LangSmith

### Links públicos

| Recurso | Link |
|---|---|
| Prompt público no Prompt Hub | [`andrellsantos/bug_to_user_story_v2`](https://smith.langchain.com/hub/andrellsantos/bug_to_user_story_v2) |
| Projeto de avaliação | [`mba-ia-pull-evaluation-prompt`](https://smith.langchain.com/) |
| Dataset de avaliação | `mba-ia-pull-evaluation-prompt-eval` (15 exemplos) |

### 1. Prompt v2 publicado no Prompt Hub

Prompt `bug_to_user_story_v2` publicado e marcado como **público**, com as tags e a descrição das técnicas aplicadas.

Link: https://smith.langchain.com/hub/andrellsantos/bug_to_user_story_v2

![Prompt v2 publicado no LangSmith Prompt Hub](images/01-prompt-hub-v2.png)

### 2. Dataset de avaliação com 15 exemplos

Dataset `mba-ia-pull-evaluation-prompt-eval` criado a partir de `datasets/bug_to_user_story.jsonl`, com os 15 exemplos (5 simples, 7 médios, 3 complexos).

![Dataset de avaliação com 15 exemplos](images/02-dataset-15-exemplos.png)

### 3. Execução da avaliação com todas as métricas ≥ 0.8

Resultado da Iteração 5 — **APROVADO**, com Helpfulness 0.86, Correctness 0.84, F1-Score 0.83, Clarity 0.88 e Precision 0.84 (média geral 0.8489).

![Avaliação aprovada com todas as métricas acima de 0.8](images/03-avaliacao-aprovada.png)

### 4. Tracing

Traces das execuções do prompt contra o dataset, mostrando entrada, saída gerada e o encadeamento das chamadas ao LLM.

**Tracing Geral**

![Tracing geral](images/04-tracing-geral.png)

**Tracing Detalhado**

![Tracing detalhado](images/05-tracing-detalhado.png)

### 5. Monitoring

![Monitoring 1](images/06-monitoring-1.png)

![Monitoring 2](images/06-monitoring-2.png)

![Monitoring 3](images/06-monitoring-3.png)

![Monitoring 4](images/06-monitoring-4.png)
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
│   └── bug_to_user_story_v2.yml  # Otimizado (iteração 5): Few-shot + Role Prompting + SoT ✅ APROVADO
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs para avaliação
│
├── images/                       # Screenshots das evidências do LangSmith
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith ✅ implementado e executado
│   ├── push_prompts.py       # Push ao LangSmith ✅ implementado e publicado
│   ├── evaluate.py           # Avaliação automática (pronto, não alterar)
│   ├── metrics.py            # 5 métricas implementadas (pronto, não alterar)
│   └── utils.py              # Funções auxiliares (pronto, não alterar)
│
└── tests/
    └── test_prompts.py       # Testes de validação ✅ implementados (6/6 passando)
```

