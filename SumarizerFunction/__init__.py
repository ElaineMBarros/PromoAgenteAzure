"""
SumarizerFunction - Azure Function para criação de resumos
Gera resumos e emails HTML de promoções
Usa o prompt summarization.md para processar
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
    from shared.utils.prompt_loader import get_summarization_prompt
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


async def create_summary(promo_data: Dict) -> str:
    """
    Cria resumo da promoção usando o prompt summarization.md
    
    Args:
        promo_data: Dados da promoção
        
    Returns:
        Resumo em formato Markdown
    """
    if not AZURE_OPENAI_KEY:
        logger.error("❌ OPENAI_API_KEY não configurada")
        return "Erro: OpenAI API Key não configurada"
    
    client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    # Carrega prompt de sumarização do arquivo .md
    try:
        if PROMPT_LOADER_AVAILABLE:
            summarization_prompt = get_summarization_prompt()
            logger.info(f"✅ Prompt summarization.md carregado ({len(summarization_prompt)} chars)")
        else:
            logger.warning("⚠️ Usando prompt fallback (prompt loader não disponível)")
            summarization_prompt = """Você é um especialista em criar resumos profissionais de promoções B2B.

Crie um resumo atraente em Markdown com:
- Título destacado
- Ícones para cada seção
- Informações organizadas
- Tom profissional

Estrutura:
# 🎯 [Título]
## 📋 Descrição
## 👥 Público-Alvo
## 📅 Período
## ✅ Condições
## 🎁 Recompensas"""
            
    except Exception as e:
        logger.error(f"❌ Erro ao carregar prompt: {e}")
        return f"Erro ao carregar prompt: {str(e)}"
    
    promo_json = json.dumps(promo_data, ensure_ascii=False, indent=2)
    user_message = f"{summarization_prompt}\n\n**DADOS DA PROMOÇÃO:**\n{promo_json}"
    
    try:
        logger.info(f"🤖 Chamando Azure OpenAI (deployment: {AZURE_OPENAI_DEPLOYMENT})")
        
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Você é um criador de resumos profissionais de promoções B2B."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        summary = response.choices[0].message.content
        logger.info(f"✅ Resumo criado ({len(summary)} chars)")
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar resumo: {str(e)}")
        return f"Erro ao criar resumo: {str(e)}"


async def create_email_html(promo_data: Dict) -> str:
    """
    Cria HTML de email da promoção
    
    Args:
        promo_data: Dados da promoção
        
    Returns:
        HTML completo do email
    """
    if not AZURE_OPENAI_KEY:
        logger.error("❌ OPENAI_API_KEY não configurada")
        return "<html><body>Erro: OpenAI API Key não configurada</body></html>"
    
    client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    prompt = """Crie um email HTML profissional e atraente para esta promoção B2B.

Requisitos:
- Design responsivo
- Cores corporativas (azul #1f3c88, branco)
- CTA claro e destacado
- Informações bem organizadas
- Layout moderno e limpo
- Compatível com clientes de email

Retorne APENAS o HTML completo, pronto para envio."""
    
    promo_json = json.dumps(promo_data, ensure_ascii=False, indent=2)
    user_message = f"{prompt}\n\n**DADOS DA PROMOÇÃO:**\n{promo_json}"
    
    try:
        logger.info(f"📧 Criando email HTML (modelo: {OPENAI_MODEL})")
        
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Você é um designer de emails HTML profissionais."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        html = response.choices[0].message.content
        
        # Remove markdown se presente
        if html.startswith("```"):
            html = html.split("```")[1]
            if html.startswith("html"):
                html = html[4:]
            html = html.strip()
        
        logger.info(f"✅ Email HTML criado ({len(html)} chars)")
        return html
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar email: {str(e)}")
        return f"<html><body><h1>Erro ao criar email</h1><p>{str(e)}</p></body></html>"


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function para criação  de resumos e emails
    
    POST /api/summarize
    
    Request Body:
    {
        "promo_data": {
            "titulo": "...",
            "mecanica": "...",
            ...
        },
        "type": "summary" ou "email"  // opcional, padrão: "summary"
    }
    
    Response (type=summary):
    {
        "success": true,
        "summary": "# 🎯 Título..."
    }
    
    Response (type=email):
    Content-Type: text/html
    <html>...</html>
    """
    logger.info('📝 SumarizerFunction: Processando requisição')
    
    try:
        req_body = req.get_json()
        promo_data = req_body.get('promo_data')
        output_type = req_body.get('type', 'summary')
        
        if not promo_data:
            logger.warning("⚠️ Campo 'promo_data' não fornecido")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": "Campo 'promo_data' é obrigatório"
                }),
                mimetype="application/json",
                status_code=400
            )
        
        logger.info(f"📋 Criando {output_type} para: {promo_data.get('titulo', 'Sem título')}")
        
        if output_type == 'email':
            # Cria email HTML
            html = await create_email_html(promo_data)
            logger.info("✅ Email HTML criado com sucesso")
            
            return func.HttpResponse(
                html,
                mimetype="text/html",
                status_code=200
            )
        else:
            # Cria resumo
            summary = await create_summary(promo_data)
            logger.info("✅ Resumo criado com sucesso")
            
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "summary": summary
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
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
        logger.error(f"❌ Erro na SumarizerFunction: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
