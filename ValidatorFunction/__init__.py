"""
ValidatorFunction - Azure Function para validação de promoções
Valida dados de promoções com regras de negócio B2B
Usa o prompt validation.md para processar
"""
import logging
import json
import os
import azure.functions as func
from openai import AsyncAzureOpenAI
from typing import Dict
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar shared
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import do prompt loader
try:
    from shared.utils.prompt_loader import get_validation_prompt
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


async def validate_promotion(promo_data: Dict) -> Dict:
    """
    Valida uma promoção usando o prompt validation.md
    
    Args:
        promo_data: Dados da promoção
        
    Returns:
        Dict com resultado da validação
    """
    if not AZURE_OPENAI_KEY:
        logger.error("❌ OPENAI_API_KEY não configurada")
        return {
            "success": False,
            "is_valid": False,
            "error": "Azure OpenAI API Key não configurada",
            "feedback": "Erro: API Key não configurada"
        }
    
    client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    # Carrega prompt de validação do arquivo .md
    try:
        if PROMPT_LOADER_AVAILABLE:
            validation_prompt = get_validation_prompt()
            logger.info(f"✅ Prompt validation.md carregado ({len(validation_prompt)} chars)")
        else:
            logger.warning("⚠️ Usando prompt fallback (prompt loader não disponível)")
            validation_prompt = """Você é um validador especializado em promoções B2B do varejo.

Analise os dados da promoção e verifique:
1. Campos obrigatórios preenchidos
2. Datas coerentes (início < fim)
3. Mecânica bem definida
4. Condições claras
5. Recompensas especificadas
6. Sem inconsistências lógicas

Retorne JSON:
{
  "is_valid": true/false,
  "status": "APROVADO" ou "REPROVADO",
  "feedback": "Mensagem detalhada",
  "issues": ["problemas"],
  "suggestions": ["sugestões"]
}"""
            
    except Exception as e:
        logger.error(f"❌ Erro ao carregar prompt: {e}")
        return {
            "success": False,
            "is_valid": False,
            "error": f"Erro ao carregar prompt: {str(e)}",
            "feedback": f"Erro ao carregar prompt: {str(e)}"
        }
    
    promo_json = json.dumps(promo_data, ensure_ascii=False, indent=2)
    user_message = f"{validation_prompt}\n\n**DADOS DA PROMOÇÃO:**\n{promo_json}"
    
    try:
        logger.info(f"🤖 Chamando Azure OpenAI (deployment: {AZURE_OPENAI_DEPLOYMENT})")
        
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Você é um validador especializado em promoções B2B. Retorne apenas JSON válido."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        logger.info(f"✅ Resposta OpenAI recebida ({len(content)} chars)")
        
        # Remove markdown se presente
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        validation_result = json.loads(content)
        
        # Log resultado
        status = validation_result.get('status', 'PENDENTE')
        is_valid = validation_result.get('is_valid', False)
        logger.info(f"{'✅' if is_valid else '❌'} Validação concluída: {status}")
        
        return {
            "success": True,
            **validation_result
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao fazer parse do JSON: {str(e)}")
        logger.error(f"Conteúdo recebido: {content[:500]}...")
        return {
            "success": False,
            "is_valid": False,
            "error": f"OpenAI retornou JSON inválido: {str(e)}",
            "feedback": "Erro ao processar resposta da validação",
            "raw_content": content[:1000]
        }
    except Exception as e:
        logger.error(f"❌ Erro na validação: {str(e)}")
        return {
            "success": False,
            "is_valid": False,
            "error": str(e),
            "feedback": f"Erro ao validar: {str(e)}"
        }


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP Trigger para validação de promoções
    
    POST /api/validate
    
    Request Body:
    {
        "promo_data": {
            "titulo": "...",
            "mecanica": "...",
            ...
        }
    }
    
    Response:
    {
        "success": true,
        "is_valid": true,
        "status": "APROVADO",
        "feedback": "Promoção válida e pronta para uso",
        "issues": [],
        "suggestions": []
    }
    """
    logger.info('✅ ValidatorFunction: Processando requisição')
    
    try:
        req_body = req.get_json()
        promo_data = req_body.get('promo_data')
        
        if not promo_data:
            logger.warning("⚠️ Campo 'promo_data' não fornecido")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "is_valid": False,
                    "error": "Campo 'promo_data' é obrigatório"
                }),
                mimetype="application/json",
                status_code=400
            )
        
        logger.info(f"📋 Validando promoção: {promo_data.get('titulo', 'Sem título')}")
        
        # Valida promoção
        result = await validate_promotion(promo_data)
        
        # Log resultado
        if result.get('success') and result.get('is_valid'):
            logger.info(f"✅ Validação bem-sucedida: {result.get('status')}")
        else:
            logger.warning(f"⚠️ Validação com problemas: {result.get('feedback')}")
        
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as e:
        logger.error(f"❌ Erro no parse do JSON: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "is_valid": False,
                "error": "JSON inválido no corpo da requisição"
            }),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.error(f"❌ Erro na ValidatorFunction: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "is_valid": False,
                "error": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
