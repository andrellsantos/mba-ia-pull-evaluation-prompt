# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Repositório do desafio de Prompt Engineering do MBA em Engenharia de Software com IA (Full Cycle). O objetivo final é fazer pull de um prompt de baixa qualidade do LangSmith Prompt Hub, otimizá-lo, publicá-lo de volta e avaliá-lo até atingir >= 0.8 em todas as métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision).

## Status atual do projeto

- [x] **Fase 1 — Pull do prompt inicial do LangSmith** (concluída, documentada abaixo)
- [x] **Fase 2 — Criação do `bug_to_user_story_v2.yml`** — versão **baseline, intencionalmente sem otimização** (cópia do v1), a pedido do usuário, para servir de ponto de comparação "antes/depois". A otimização de fato (Few-shot + técnica adicional) fica para uma iteração futura.
- [x] **Fase 3 — `src/push_prompts.py` implementado** — publicação no Hub e avaliação (`src/evaluate.py`) devem ser **executadas manualmente pelo usuário** (ver instruções abaixo), pois são ações que publicam dados publicamente / em um projeto compartilhado do LangSmith.
- [ ] Fase 4 — Iteração até atingir as métricas mínimas (não se aplica ainda, pois o v2 é deliberadamente igual ao v1)
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

## Fase 2 — Criação do `bug_to_user_story_v2.yml` (baseline, sem otimização)

**Importante:** a pedido do usuário, esta versão do v2 é uma **cópia fiel do v1**, sem nenhuma técnica de Prompt Engineering aplicada ainda. O objetivo aqui não é otimizar, e sim ter uma versão v2 publicável no Hub para rodar a avaliação (Fase 3) e obter os scores de baseline "ruins" — a mesma referência de partida (métricas ~0.45-0.52) mostrada no exemplo do enunciado. A otimização real (Few-shot obrigatório + CoT/ToT/SoT/ReAct/Role Prompting) fica para uma iteração seguinte, depois de vermos os números.

O arquivo [`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml) foi criado com:

- A mesma `system_prompt` e `user_prompt` do v1 (nenhum texto foi alterado)
- `version: "v2"` e `source: "leonanluppi/bug_to_user_story_v1"` (rastreabilidade de que ainda é a versão-base)
- `techniques_applied: []` (vazio — nenhuma técnica aplicada nesta rodada, propositalmente)

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

### Resultado esperado

Como o v2 é idêntico ao prompt "ruim" do enunciado, o esperado é que a avaliação **reprove** (métricas próximas de 0.45–0.55, como no exemplo ilustrativo do desafio). Isso é intencional: serve de baseline documentado antes de aplicarmos as técnicas de otimização na próxima iteração (Fase 4).

*(Após você rodar os dois comandos acima, me avise o resultado — ou cole a saída do terminal — que eu atualizo esta seção com os números reais e os links/screenshots do dashboard.)*

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
│   └── bug_to_user_story_v2.yml  # Baseline sem otimização (Fase 2) ✅ — otimização real ainda pendente
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

- **Pendente (você):** rodar `python src/push_prompts.py` e depois `python src/evaluate.py` (veja a seção "Fase 3" acima) para obter os scores de baseline do v2.
- **Fase 4 (otimização real):** com os scores de baseline em mãos, reescrever `prompts/bug_to_user_story_v2.yml` aplicando Few-shot Learning (obrigatório) + pelo menos mais uma técnica (CoT, ToT, SoT, ReAct ou Role Prompting), e repetir push + avaliação (3-5 iterações) até todas as 5 métricas ficarem >= 0.8.
- **Fase 5:** implementar os 6 testes em `tests/test_prompts.py` e validar com `pytest tests/test_prompts.py`.
