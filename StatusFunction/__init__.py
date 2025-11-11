"""
StatusFunction - Retorna status do sistema
Endpoint: GET /api/status
"""
import azure.functions as func
import json
import os
import logging

logger = logging.getLogger(__name__)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint de status do sistema
    Verifica Azure OpenAI, Cosmos DB e Blob Storage
    """
    logger.info('StatusFunction processando requisição')
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS (preflight)
    if req.method == 'OPTIONS':
        return func.HttpResponse("", status_code=200, headers=headers)
    
    try:
        # Verificar serviços Azure
        openai_ok = bool(os.environ.get("AZURE_OPENAI_API_KEY"))
        cosmos_ok = bool(os.environ.get("COSMOS_ENDPOINT"))
        blob_ok = bool(os.environ.get("AZURE_STORAGE_CONNECTION_STRING"))
        
        # TODO: Buscar contagens reais do Cosmos DB
        messages_stored = 0
        promotions_count = 0
        
        # Montar resposta de status
        status = {
            "system_ready": openai_ok and cosmos_ok,
            "openai": openai_ok,
            "openai_model": "gpt-4o-mini",
            "cosmos_db": cosmos_ok,
            "blob_storage": blob_ok,
            "messages_stored": messages_stored,
            "promotions_count": promotions_count,
            "environment": "azure"
        }
        
        logger.info(f"Status check: OpenAI={openai_ok}, Cosmos={cosmos_ok}, Blob={blob_ok}")
        
        return func.HttpResponse(
            json.dumps(status),
            status_code=200,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Erro no StatusFunction: {e}")
        return func.HttpResponse(
            json.dumps({
                "error": "Erro ao verificar status",
                "details": str(e)
            }),
            status_code=500,
            headers=headers
        )
