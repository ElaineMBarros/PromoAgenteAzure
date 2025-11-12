"""
Utilitário para carregar prompts markdown nas Azure Functions
"""
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Encontra o diretório de prompts relativo a este arquivo
# shared/utils/prompt_loader.py -> vai para ../../prompts
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

def load_prompt(prompt_name: str, inject_date: bool = True) -> str:
    """
    Carrega um prompt .md do diretório de prompts
    
    Args:
        prompt_name: Nome do arquivo sem extensão (ex: 'extraction')
        inject_date: Se True, substitui {current_date} pela data atual
        
    Returns:
        Conteúdo do prompt como string
        
    Raises:
        FileNotFoundError: Se o prompt não existir
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"
    
    if not prompt_path.exists():
        logger.error(f"Prompt não encontrado: {prompt_path}")
        raise FileNotFoundError(
            f"Prompt '{prompt_name}' não encontrado em {PROMPTS_DIR}"
        )
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Injeta data atual se necessário
        if inject_date and '{current_date}' in content:
            current_date = datetime.now().strftime("%d/%m/%Y")
            content = content.replace('{current_date}', current_date)
            logger.info(f"Data injetada no prompt: {current_date}")
        
        logger.info(f"Prompt '{prompt_name}' carregado com sucesso ({len(content)} chars)")
        return content
        
    except Exception as e:
        logger.error(f"Erro ao ler prompt '{prompt_name}': {e}")
        raise


def get_extraction_prompt() -> str:
    """Carrega o prompt de extração com data atual injetada"""
    return load_prompt("extraction", inject_date=True)


def get_validation_prompt() -> str:
    """Carrega o prompt de validação com data atual injetada"""
    return load_prompt("validation", inject_date=True)


def get_summarization_prompt() -> str:
    """Carrega o prompt de sumarização"""
    return load_prompt("summarization", inject_date=False)


def get_persona_prompt() -> str:
    """Carrega o prompt de persona"""
    return load_prompt("persona", inject_date=False)


def list_available_prompts() -> list:
    """Lista todos os prompts .md disponíveis"""
    if not PROMPTS_DIR.exists():
        return []
    
    prompts = [
        p.stem for p in PROMPTS_DIR.glob("*.md")
    ]
    logger.info(f"Prompts disponíveis: {prompts}")
    return prompts


# Cache de prompts (opcional - economiza I/O)
_PROMPT_CACHE = {}

def get_cached_prompt(prompt_name: str, inject_date: bool = True) -> str:
    """
    Versão com cache do load_prompt
    Útil para reduzir I/O em execuções rápidas
    """
    cache_key = f"{prompt_name}_{inject_date}"
    
    if cache_key not in _PROMPT_CACHE:
        _PROMPT_CACHE[cache_key] = load_prompt(prompt_name, inject_date)
    
    return _PROMPT_CACHE[cache_key]


def clear_prompt_cache():
    """Limpa o cache de prompts (útil para testes)"""
    global _PROMPT_CACHE
    _PROMPT_CACHE = {}
    logger.info("Cache de prompts limpo")


# Validação ao importar o módulo
def _validate_prompts_directory():
    """Valida que o diretório de prompts existe"""
    if not PROMPTS_DIR.exists():
        logger.warning(
            f"⚠️ Diretório de prompts não encontrado: {PROMPTS_DIR}\n"
            f"   Certifique-se que a pasta 'prompts/' existe na raiz do projeto"
        )
        return False
    
    prompts = list_available_prompts()
    required_prompts = ['extraction', 'validation', 'summarization', 'persona']
    missing = [p for p in required_prompts if p not in prompts]
    
    if missing:
        logger.warning(f"⚠️ Prompts faltando: {missing}")
        return False
    
    logger.info(f"✅ Todos os prompts necessários encontrados: {prompts}")
    return True


# Executa validação ao importar
_validate_prompts_directory()
