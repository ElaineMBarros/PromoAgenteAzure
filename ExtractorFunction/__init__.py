"""
ExtractorFunction - Azure Function para extração de informações
Extrai dados estruturados de texto não estruturado sobre promoções
Usa o prompt extraction.md para processar
"""
import logging
import json
import os
import azure.functions as func
from openai import AsyncAzureOpenAI
from typing import Dict, Any
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar shared
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import do prompt loader
try:
    from shared.utils.prompt_loader import get_extraction_prompt
    PROMPT_LOADER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Prompt loader não disponível: {e}")
    PROMPT_LOADER_AVAILABLE = False

# Configuração Azure OpenAI
AZURE_OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("OPENAI_API_ENDPOINT", "https://eastus.api.cognitive.microsoft.com/")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"

logger = logging.getLogger(__name__)


async def extract_promo_info(text: str, current_state: Dict = None) -> Dict:
    """
    Extrai informações de promoção do texto usando o prompt extraction.md
    
    Args:
        text: Texto do usuário
        current_state: Estado atual da promoção (opcional)
        
    Returns:
        Dict com informações extraídas
    """
    if not AZURE_OPENAI_KEY:
        logger.error("❌ AZURE_OPENAI_KEY não configurada")
        return {
            "success": False,
            "error": "Azure OpenAI API Key não configurada",
            "data": None
        }
    
    # Cliente Azure OpenAI
    client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    # Carrega prompt de extração do arquivo .md
    try:
        if PROMPT_LOADER_AVAILABLE:
            extraction_prompt = get_extraction_prompt()
            logger.info(f"✅ Prompt extraction.md carregado ({len(extraction_prompt)} chars)")
        else:
            logger.warning("⚠️ Usando prompt fallback (prompt loader não disponível)")
            extraction_prompt = """Você é um especialista em Promoções de Trade Marketing B2B.
Sua missão é APENAS extrair e estruturar dados de promoções.

Extraia informações e retorne em formato JSON com os seguintes campos:
- titulo, mecanica, descricao, segmentacao
- periodo_inicio, periodo_fim (formato DD/MM/YYYY)
- condicoes, recompensas, produtos, categorias
- volume_minimo, desconto_percentual

Use null para campos não mencionados. Seja preciso e objetivo."""
            
    except Exception as e:
        logger.error(f"❌ Erro ao carregar prompt: {e}")
        return {
            "success": False,
            "error": f"Erro ao carregar prompt: {str(e)}",
            "data": None
        }
    
    # Adiciona contexto se houver estado atual
    context_message = ""
    if current_state:
        context_message = f"\n\n**ESTADO ATUAL DA PROMOÇÃO:**\n{json.dumps(current_state, ensure_ascii=False, indent=2)}"
    
    user_message = f"{context_message}\n\n**TEXTO DO USUÁRIO:**\n{text}"
    
    try:
        logger.info(f"🤖 Chamando Azure OpenAI (deployment: {AZURE_OPENAI_DEPLOYMENT})")
        
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content
        logger.info(f"✅ Resposta OpenAI recebida ({len(content)} chars)")
        
        # Remove markdown se presente
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        extracted_data = json.loads(content)
        
        # Detecta múltiplas promoções
        is_multiple = isinstance(extracted_data, list)
        
        # MERGE com estado atual se fornecido
        if current_state and not is_multiple:
            # Merge: mantém dados antigos, adiciona/sobrescreve com novos
            merged_data = {**current_state, **extracted_data}
            # Remove campos null/vazios dos novos dados para não sobrescrever com vazio
            for key, value in extracted_data.items():
                if value is None or value == "" or value == []:
                    # Se o novo valor é vazio, mantém o antigo
                    if key in current_state:
                        merged_data[key] = current_state[key]
            extracted_data = merged_data
            logger.info(f"✅ Merge realizado com estado atual")
        
        logger.info(f"✅ Extração concluída: {1 if not is_multiple else len(extracted_data)} promoção(ões)")
        
        return {
            "success": True,
            "data": extracted_data,
            "is_multiple": is_multiple,
            "count": len(extracted_data) if is_multiple else 1
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao fazer parse do JSON: {str(e)}")
        logger.error(f"Conteúdo recebido: {content[:500]}...")
        return {
            "success": False,
            "error": f"OpenAI retornou JSON inválido: {str(e)}",
            "data": None,
            "raw_content": content[:1000]
        }
    except Exception as e:
        logger.error(f"❌ Erro na extração: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP Trigger para extração de informações
    
    POST /api/extract
    
    Request Body:
    {
        "text": "Texto com informações da promoção",
        "current_state": {} // opcional - estado atual para contexto
    }
    
    Response:
    {
        "success": true,
        "data": {...} or [...],
        "is_multiple": false,
        "count": 1
    }
    """
    logger.info('🔍 ExtractorFunction: Processando requisição')
    
    try:
        # Parse request body
        req_body = req.get_json()
        text = req_body.get('text')
        current_state = req_body.get('current_state')
        
        if not text:
            logger.warning("⚠️ Campo 'text' não fornecido")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": "Campo 'text' é obrigatório"
                }),
                mimetype="application/json",
                status_code=400
            )
        
        logger.info(f"📝 Texto recebido ({len(text)} chars)")
        if current_state:
            logger.info(f"📋 Estado atual fornecido")
        
        # Extrai informações
        result = await extract_promo_info(text, current_state)
        
        # Log resultado
        if result.get('success'):
            logger.info(f"✅ Extração bem-sucedida")
        else:
            logger.error(f"❌ Extração falhou: {result.get('error')}")
        
        # Retorna resultado
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if result.get('success') else 500
        )
        
    except ValueError as e:
        logger.error(f"❌ Erro no parse do JSON: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": "JSON inválido no corpo da requisição"
            }),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.error(f"❌ Erro na ExtractorFunction: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
