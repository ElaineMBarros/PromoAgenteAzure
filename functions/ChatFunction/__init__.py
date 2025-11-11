"""
ChatFunction - Orquestrador principal do PromoAgente
Endpoint: POST /api/chat
Usa Agno para orquestrar todo o fluxo de criação de promoções
"""
import azure.functions as func
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint principal de chat com IA
    Recebe mensagens do usuário e processa com Agno + OpenAI
    """
    logger.info('ChatFunction processando requisição')
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS (preflight)
    if req.method == 'OPTIONS':
        return func.HttpResponse("", status_code=200, headers=headers)
    
    try:
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON"}),
                status_code=400,
                headers=headers
            )
        
        # Validar campos obrigatórios
        message = req_body.get('message')
        if not message:
            return func.HttpResponse(
                json.dumps({"error": "Campo 'message' é obrigatório"}),
                status_code=400,
                headers=headers
            )
        
        session_id = req_body.get('session_id') or f"session_{datetime.utcnow().timestamp()}"
        
        # Importar agno e inicializar agente
        try:
            from agno import Agent
            
            # Configurar OpenAI
            openai_key = os.environ.get("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY não configurada")
            
            # Criar agente Agno
            promo_agent = Agent(
                name="PromoAgente",
                model="gpt-4o-mini",
                api_key=openai_key,
                instructions="""
                Você é um especialista em promoções B2B para o setor de bebidas.
                Seu papel é ajudar a criar promoções comerciais detalhadas.
                
                Tipos de mecânicas:
                - Progressiva: desconto aumenta com volume
                - Volume: desconto fixo por volume mínimo
                - Kit: combo de produtos
                - Cashback: devolução de valor
                - Bonificação: produtos grátis
                
                Informações necessárias:
                1. Título da promoção
                2. Mecânica (tipo)
                3. Descrição completa
                4. Segmentação (público-alvo)
                5. Período (início e fim)
                6. Condições de participação
                7. Recompensas/benefícios
                8. Produtos envolvidos
                9. Volumes/quantidades mínimas
                
                Seja conversacional e guie o usuário passo a passo.
                Faça perguntas claras e objetivas.
                Valide informações e sugira melhorias.
                """,
                markdown=True
            )
            
            # TODO: Implementar gestão de contexto com Cosmos DB
            # Por enquanto, resposta simples
            
            # Processar mensagem com Agno
            response_text = promo_agent.run(message)
            
            # Preparar resposta
            response_data = {
                "response": response_text,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
            return func.HttpResponse(
                json.dumps(response_data, ensure_ascii=False),
                status_code=200,
                headers=headers
            )
            
        except ImportError as e:
            logger.error(f"Erro ao importar agno: {e}")
            return func.HttpResponse(
                json.dumps({
                    "error": "Biblioteca Agno não disponível",
                    "details": str(e)
                }),
                status_code=500,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Erro ao processar com Agno: {e}")
            return func.HttpResponse(
                json.dumps({
                    "error": "Erro ao processar mensagem com IA",
                    "details": str(e)
                }),
                status_code=500,
                headers=headers
            )
    
    except Exception as e:
        logger.error(f"Erro geral na ChatFunction: {e}")
        return func.HttpResponse(
            json.dumps({
                "error": "Erro interno no servidor",
                "details": str(e)
            }),
            status_code=500,
            headers=headers
        )
