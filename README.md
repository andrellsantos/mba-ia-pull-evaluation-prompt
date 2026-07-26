# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Repositório do desafio de Prompt Engineering do MBA em Engenharia de Software com IA (Full Cycle). O objetivo final é fazer pull de um prompt de baixa qualidade do LangSmith Prompt Hub, otimizá-lo, publicá-lo de volta e avaliá-lo até atingir >= 0.8 em todas as métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision).

## Status atual do projeto

- [x] **Fase 1 — Pull do prompt inicial do LangSmith** (concluída, documentada abaixo)
- [ ] Fase 2 — Otimização do prompt (`prompts/bug_to_user_story_v2.yml`)
- [ ] Fase 3 — Push do prompt otimizado e avaliação (`src/push_prompts.py`, `src/evaluate.py`)
- [ ] Fase 4 — Iteração até atingir as métricas mínimas
- [ ] Fase 5 — Testes de validação (`tests/test_prompts.py`)

Este README documenta em detalhes o que já foi implementado e executado (Fase 1) e será atualizado conforme as próximas fases forem concluídas.

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

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example              # Template das variáveis de ambiente
├── requirements.txt          # Dependências Python
├── README.md                 # Este arquivo
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial (pull do LangSmith Hub) ✅
│   └── bug_to_user_story_v2.yml  # Prompt otimizado (Fase 2, pendente)
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs para avaliação
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith ✅ implementado
│   ├── push_prompts.py       # Push ao LangSmith (Fase 3, pendente)
│   ├── evaluate.py           # Avaliação automática (pronto, não alterar)
│   ├── metrics.py            # 5 métricas implementadas (pronto, não alterar)
│   └── utils.py              # Funções auxiliares (pronto, não alterar)
│
└── tests/
    └── test_prompts.py       # Testes de validação (Fase 5, pendente)
```

## Próximos passos

- **Fase 2:** analisar `prompts/bug_to_user_story_v1.yml` e criar `prompts/bug_to_user_story_v2.yml` aplicando Few-shot Learning (obrigatório) + pelo menos mais uma técnica (CoT, ToT, SoT, ReAct ou Role Prompting).
- **Fase 3:** implementar `src/push_prompts.py`, publicar o v2 publicamente no LangSmith Hub e rodar `src/evaluate.py`.
- **Fase 4:** iterar (3-5 rodadas) até todas as 5 métricas ficarem >= 0.8.
- **Fase 5:** implementar os 6 testes em `tests/test_prompts.py` e validar com `pytest tests/test_prompts.py`.
