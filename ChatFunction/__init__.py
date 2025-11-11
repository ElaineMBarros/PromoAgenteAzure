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


def should_extract_data(ai_response: str, user_message: str, history: list) -> bool:
    """
    Detecta se deve chamar extraction.md para estruturar dados
    """
    # Marcadores na resposta da IA
    if "✅ Dados registrados" in ai_response:
        return True
    
    if "Confirma os dados" in ai_response:
        return True
    
    # Usuário confirmando
    user_lower = user_message.lower()
    confirms = ['confirmo', 'sim', 'está certo', 'correto', 'pode salvar', 'ok', 'confirma']
    if any(word in user_lower for word in confirms):
        # Só confirma se já tem dados na conversa
        if len(history) > 2:  # Tem pelo menos 2 trocas de mensagens
            return True
    
    return False


async def extract_structured_data(client, extraction_prompt: str, history: list, current_message: str):
    """
    Usa extraction.md para extrair dados estruturados
    """
    # Montar contexto completo da conversa
    conversation_parts = []
    for msg in history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        conversation_parts.append(f"{role}: {content}")
    
    conversation_parts.append(f"user: {current_message}")
    full_conversation = "\n\n".join(conversation_parts)
    
    # Adicionar data atual ao prompt
    current_date = datetime.utcnow().strftime("%d/%m/%Y")
    extraction_with_date = extraction_prompt.replace("{current_date}", current_date)
    
    # Chamar OpenAI para extrair
    try:
        extract_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": extraction_with_date},
                {"role": "user", "content": f"Extraia os dados estruturados desta conversa:\n\n{full_conversation}"}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Parse JSON
        extracted_text = extract_response.choices[0].message.content
        
        # Tentar encontrar JSON no texto
        if '{' in extracted_text:
            start = extracted_text.index('{')
            end = extracted_text.rindex('}') + 1
            json_str = extracted_text[start:end]
            extracted_data = json.loads(json_str)
            return extracted_data
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados: {e}")
        return None


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
        
        # Inicializar Cosmos DB
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from shared.adapters.cosmos_adapter import cosmos_adapter
            
            # Criar sessão se não existir
            await cosmos_adapter.create_session(session_id)
            
            # Buscar histórico da conversa
            history = await cosmos_adapter.get_recent_messages(session_id, limit=10)
            
        except Exception as e:
            logger.warning(f"Cosmos DB não disponível: {e}")
            history = []
        
        # Usar Azure OpenAI Service
        try:
            from openai import AzureOpenAI
            
            # Configurar Azure OpenAI
            azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            azure_key = os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
            azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            
            if not azure_endpoint or not azure_key:
                raise ValueError("Azure OpenAI não configurado corretamente")
            
            # Criar cliente Azure OpenAI
            client = AzureOpenAI(
                api_key=azure_key,
                api_version=api_version,
                azure_endpoint=azure_endpoint
            )
            
            # Carregar prompt persona do arquivo
            prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'persona.md')
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read()
            except:
                # Fallback se arquivo não existir
                system_prompt = """
                Você é o PromoAgente, assistente especializado em coletar e registrar dados de promoções B2B.
                Sua única função é COLETAR → INTERPRETAR → REGISTRAR dados de promoções.
                Seja direto, objetivo e focado em coletar informações da promoção.
                Não responda perguntas conceituais, apenas colete dados da promoção.
                """
            
            # Montar contexto completo com histórico
            messages = [{"role": "system", "content": system_prompt.strip()}]
            
            # Adicionar histórico da conversa
            if history:
                messages.extend(history)
                logger.info(f"Carregado {len(history)} mensagens do histórico")
            
            # Adicionar mensagem atual
            messages.append({"role": "user", "content": message})
            
            # Processar mensagem com OpenAI
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content
            
            # ORQUESTRAÇÃO: Detectar se deve extrair dados estruturados
            if should_extract_data(response_text, message, history):
                logger.info("🔍 Detectado dados para extração - chamando extraction.md")
                
                # Carregar prompt extraction
                extraction_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'extraction.md')
                try:
                    with open(extraction_path, 'r', encoding='utf-8') as f:
                        extraction_prompt = f.read()
                    
                    # Extrair dados estruturados
                    extracted_data = await extract_structured_data(
                        client,
                        extraction_prompt,
                        history,
                        message
                    )
                    
                    if extracted_data:
                        # Adicionar metadata
                        extracted_data['session_id'] = session_id
                        extracted_data['created_at'] = datetime.utcnow().isoformat()
                        extracted_data['promo_id'] = f"promo_{datetime.utcnow().timestamp()}"
                        
                        # Salvar no Cosmos DB
                        try:
                            if cosmos_adapter and cosmos_adapter.client:
                                await cosmos_adapter.save_promotion(extracted_data)
                                logger.info(f"✅ Promoção salva: {extracted_data.get('titulo', 'sem título')}")
                        except Exception as e:
                            logger.error(f"Erro ao salvar promoção: {e}")
                    
                except Exception as e:
                    logger.error(f"Erro ao carregar extraction.md: {e}")
            
            # Salvar mensagens no Cosmos DB
            try:
                if cosmos_adapter and cosmos_adapter.client:
                    await cosmos_adapter.save_message(session_id, message, response_text)
                    logger.info(f"Mensagens salvas no Cosmos DB para session {session_id}")
            except Exception as e:
                logger.warning(f"Erro ao salvar mensagens no Cosmos DB: {e}")
            
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
