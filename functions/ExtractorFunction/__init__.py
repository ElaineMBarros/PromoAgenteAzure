"""
ExtractorFunction - Azure Function para extração de informações
Extrai dados estruturados de texto não estruturado sobre promoções
"""
import logging
import json
import os
import azure.functions as func
from openai import AsyncOpenAI
from typing import Dict, Any

# Configuração
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


async def extract_promo_info(text: str, current_state: Dict = None) -> Dict:
    """
    Extrai informações de promoção do texto
    
    Args:
        text: Texto do usuário
        current_state: Estado atual da promoção (opcional)
        
    Returns:
        Dict com informações extraídas
    """
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    # Carrega prompt de extração
    prompt = """Você é um assistente especializado em extrair informações de promoções B2B do varejo.

Extraia as seguintes informações do texto fornecido e retorne em formato JSON:

{
  "titulo": "Título da promoção (se mencionado)",
  "mecanica": "Tipo de mecânica (progressiva, casada, pontos, relâmpago, escalonada, VIP)",
  "descricao": "Descrição de como funciona",
  "segmentacao": "Público-alvo ou segmento de clientes",
  "periodo_inicio": "Data de início (formato: DD/MM/YYYY ou descrição)",
  "periodo_fim": "Data de fim (formato: DD/MM/YYYY ou descrição)",
  "condicoes": "Condições e regras de ativação",
  "recompensas": "Benefícios e recompensas oferecidas",
  "produtos": ["lista", "de", "produtos"],
  "categorias": ["lista", "de", "categorias"],
  "volume_minimo": "Volume mínimo se aplicável",
  "desconto_percentual": "Percentual de desconto se aplicável"
}

IMPORTANTE:
- Só preencha campos que estão CLARAMENTE mencionados no texto
- Use null para campos não mencionados
- Seja preciso e objetivo
- Mantenha o contexto B2B de varejo
- Se houver múltiplas promoções, retorne um array de objetos"""
    
    # Adiciona contexto se houver estado atual
    context = ""
    if current_state:
        context = f"\n\n**CONTEXTO ATUAL DA PROMOÇÃO:**\n{json.dumps(current_state, ensure_ascii=False, indent=2)}"
    
    full_prompt = f"{prompt}{context}\n\n**TEXTO DO USUÁRIO:**\n{text}"
    
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em extrair informações de promoções B2B. Retorne apenas JSON válido."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Remove markdown se presente
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        extracted_data = json.loads(content)
        
        return {
            "success": True,
            "data": extracted_data,
            "is_multiple": isinstance(extracted_data, list)
        }
        
    except Exception as e:
        logging.error(f"Erro na extração: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP Trigger para extração de informações
    
    Request Body:
    {
        "text": "Texto com informações da promoção",
        "current_state": {} // opcional
    }
    
    Response:
    {
        "success": true,
        "data": {...},
        "is_multiple": false
    }
    """
    logging.info('ExtractorFunction: Processando requisição')
    
    try:
        # Parse request body
        req_body = req.get_json()
        text = req_body.get('text')
        current_state = req_body.get('current_state')
        
        if not text:
            return func.HttpResponse(
                json.dumps({"error": "Campo 'text' é obrigatório"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Extrai informações
        result = await extract_promo_info(text, current_state)
        
        # Retorna resultado
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if result.get('success') else 500
        )
        
    except ValueError as e:
        logging.error(f"Erro no parse do JSON: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "JSON inválido no corpo da requisição"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Erro na ExtractorFunction: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
