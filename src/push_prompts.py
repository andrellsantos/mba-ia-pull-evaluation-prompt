"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

# Evita UnicodeEncodeError ao imprimir emojis (✅/❌) no console do Windows (cp1252)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PROMPTS_FILE = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (ex: "bug_to_user_story_v2")
        prompt_data: Dados do prompt (contém system_prompt, user_prompt, description, tags, techniques_applied)

    Returns:
        True se sucesso, False caso contrário
    """
    template = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data.get("description", "")
    if techniques:
        description = f"{description} | Técnicas aplicadas: {', '.join(techniques)}"

    tags = prompt_data.get("tags", [])

    try:
        url = hub.push(
            prompt_name,
            template,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=tags,
        )
        print(f"✅ Prompt publicado com sucesso: {url}")
        return True
    except Exception as e:
        print(f"❌ Erro ao publicar prompt '{prompt_name}' no LangSmith Hub: {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    for field in ("description", "system_prompt", "user_prompt", "version"):
        if not prompt_data.get(field):
            errors.append(f"Campo obrigatório ausente ou vazio: {field}")

    system_prompt = prompt_data.get("system_prompt", "")
    if "[TODO]" in system_prompt or "TODO" in system_prompt:
        errors.append("system_prompt ainda contém marcações de TODO")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    print_section_header(f"Fazendo push do prompt: {PROMPT_KEY}")

    prompts = load_yaml(PROMPTS_FILE)
    if not prompts or PROMPT_KEY not in prompts:
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPTS_FILE}")
        return 1

    prompt_data = prompts[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    success = push_prompt_to_langsmith(PROMPT_KEY, prompt_data)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
