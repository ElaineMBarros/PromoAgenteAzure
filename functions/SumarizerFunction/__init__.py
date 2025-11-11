"""
SumarizerFunction - Azure Function para criação de resumos
Gera resumos e emails HTML de promoções
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


async def create_summary(promo_data: Dict) -> str:
    """Cria resumo da promoção em Markdown"""
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    prompt = """Você é um especialista em criar resumos profissionais de promoções B2B.

Crie um resumo atraente e profissional em formato Markdown com:
- Título destacado
- Ícones para cada seção
- Informações organizadas
- Tom profissional mas entusiasta

Estrutura sugerida:
# 🎯 [Título]
## 📋 Descrição
## 👥 Público-Alvo
## 📅 Período
## ✅ Condições
## 🎁 Recompensas
## 📊 Detalhes Adicionais"""
    
    promo_json = json.dumps(promo_data, ensure_ascii=False, indent=2)
    
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um criador de resumos profissionais de promoções."},
                {"role": "user", "content": f"{prompt}\n\n**DADOS:**\n{promo_json}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"Erro ao criar resumo: {str(e)}")
        return f"Erro ao criar resumo: {str(e)}"


async def create_email_html(promo_data: Dict) -> str:
    """Cria HTML de email da promoção"""
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    prompt = """Crie um email HTML profissional e atraente para esta promoção B2B.

Requisitos:
- Design responsivo
- Cores corporativas (azul, branco)
- CTA claro
- Informações bem organizadas
- Layout moderno

Retorne APENAS o HTML completo, pronto para envio."""
    
    promo_json = json.dumps(promo_data, ensure_ascii=False, indent=2)
    
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um designer de emails HTML profissionais."},
                {"role": "user", "content": f"{prompt}\n\n**DADOS:**\n{promo_json}"}
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
        
        return html
        
    except Exception as e:
        logging.error(f"Erro ao criar email: {str(e)}")
        return f"<html><body>Erro ao criar email: {str(e)}</body></html>"


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function para criação de resumos e emails
    
    Request Body:
    {
        "promo_data": {...},
        "type": "summary" ou "email"
    }
    """
    logging.info('SumarizerFunction: Processando requisição')
    
    try:
        req_body = req.get_json()
        promo_data = req_body.get('promo_data')
        output_type = req_body.get('type', 'summary')
        
        if not promo_data:
            return func.HttpResponse(
                json.dumps({"error": "Campo 'promo_data' é obrigatório"}),
                mimetype="application/json",
                status_code=400
            )
        
        if output_type == 'email':
            # Cria email HTML
            html = await create_email_html(promo_data)
            return func.HttpResponse(
                html,
                mimetype="text/html",
                status_code=200
            )
        else:
            # Cria resumo
            summary = await create_summary(promo_data)
            return func.HttpResponse(
                json.dumps({"summary": summary}, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )
        
    except ValueError as e:
        logging.error(f"Erro no parse do JSON: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "JSON inválido"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Erro na SumarizerFunction: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
