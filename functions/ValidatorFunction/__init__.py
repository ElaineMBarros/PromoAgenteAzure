"""
ValidatorFunction - Azure Function para validação de promoções
Valida dados de promoções com regras de negócio B2B
"""
import logging
import json
import os
import azure.functions as func
from openai import AsyncOpenAI
from typing import Dict

# Configuração
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


async def validate_promotion(promo_data: Dict) -> Dict:
    """
    Valida uma promoção usando IA
    
    Args:
        promo_data: Dados da promoção
        
    Returns:
        Dict com resultado da validação
    """
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    prompt = """Você é um assistente especializado em validar promoções B2B do varejo.

Analise os dados da promoção e verifique:
1. Todos os campos obrigatórios estão preenchidos
2. As datas são coerentes (início < fim)
3. A mecânica está bem definida
4. As condições são claras e aplicáveis
5. As recompensas estão bem especificadas
6. Não há inconsistências lógicas

Retorne um JSON com:
{
  "is_valid": true/false,
  "status": "APROVADO" ou "REPROVADO",
  "feedback": "Mensagem detalhada",
  "issues": ["lista de problemas encontrados (se houver)"],
  "suggestions": ["sugestões de melhoria (opcional)"]
}"""
    
    promo_json = json.dumps(promo_data, ensure_ascii=False, indent=2)
    
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um validador especializado em promoções B2B. Retorne apenas JSON válido."},
                {"role": "user", "content": f"{prompt}\n\n**DADOS DA PROMOÇÃO:**\n{promo_json}"}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        
        # Remove markdown se presente
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        validation_result = json.loads(content)
        
        return {
            "success": True,
            **validation_result
        }
        
    except Exception as e:
        logging.error(f"Erro na validação: {str(e)}")
        return {
            "success": False,
            "is_valid": False,
            "error": str(e),
            "feedback": f"Erro ao validar: {str(e)}"
        }


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP Trigger para validação de promoções
    
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
        "feedback": "..."
    }
    """
    logging.info('ValidatorFunction: Processando requisição')
    
    try:
        req_body = req.get_json()
        promo_data = req_body.get('promo_data')
        
        if not promo_data:
            return func.HttpResponse(
                json.dumps({"error": "Campo 'promo_data' é obrigatório"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Valida promoção
        result = await validate_promotion(promo_data)
        
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as e:
        logging.error(f"Erro no parse do JSON: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "JSON inválido no corpo da requisição"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Erro na ValidatorFunction: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
