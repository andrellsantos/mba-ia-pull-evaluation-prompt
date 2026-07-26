"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    prompts = load_prompts(PROMPT_FILE)
    return prompts[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data["system_prompt"]
        assert "Você é um" in system_prompt
        assert "Product Manager" in system_prompt

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"]
        assert "Como um" in system_prompt
        assert "Critérios de Aceitação" in system_prompt
        assert "Markdown" in system_prompt

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"]
        assert system_prompt.count("## Exemplo") >= 2
        assert system_prompt.count("Relato:") >= 2
        assert system_prompt.count("Resposta:") >= 2

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        assert "TODO" not in prompt_data["system_prompt"]
        assert "TODO" not in prompt_data.get("user_prompt", "")

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert len(techniques) >= 2, f"Esperado >= 2 técnicas, encontradas: {techniques}"

        is_valid, errors = validate_prompt_structure(prompt_data)
        assert not any("técnicas" in error.lower() for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])