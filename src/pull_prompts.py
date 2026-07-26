"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Evita UnicodeEncodeError ao imprimir emojis (✅/❌) no console do Windows (cp1252)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PROMPT_HUB_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"


def _extract_template_text(message) -> str:
    """
    Extrai o texto de template de uma mensagem de um ChatPromptTemplate,
    cobrindo tanto objetos *MessagePromptTemplate quanto mensagens simples.
    """
    prompt = getattr(message, "prompt", None)
    if prompt is not None and hasattr(prompt, "template"):
        return prompt.template
    if hasattr(message, "content"):
        return message.content
    return str(message)


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt `leonanluppi/bug_to_user_story_v1` do LangSmith Prompt Hub
    e salva o resultado em prompts/bug_to_user_story_v1.yml.

    Returns:
        True se sucesso, False caso contrário
    """
    print_section_header(f"Fazendo pull do prompt: {PROMPT_HUB_NAME}")

    try:
        prompt = hub.pull(PROMPT_HUB_NAME)
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt '{PROMPT_HUB_NAME}': {e}")
        return False

    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt, "messages", None)
    if messages:
        for message in messages:
            role = type(message).__name__.lower()
            text = _extract_template_text(message)
            if "system" in role:
                system_prompt = text
            elif "human" in role or "user" in role:
                user_prompt = text
    else:
        # Fallback: PromptTemplate simples (sem mensagens system/human separadas)
        system_prompt = getattr(prompt, "template", str(prompt))

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories (pull do LangSmith Hub)",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "source": PROMPT_HUB_NAME,
        }
    }

    success = save_yaml(prompt_data, str(OUTPUT_FILE))

    if success:
        print(f"✅ Prompt salvo em: {OUTPUT_FILE}")
    else:
        print("❌ Falha ao salvar o prompt localmente.")

    return success


def main():
    """Função principal"""
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    success = pull_prompts_from_langsmith()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
