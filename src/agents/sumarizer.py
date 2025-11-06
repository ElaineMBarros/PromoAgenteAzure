"""
SumarizerAgent - Cria resumos profissionais de promoções
"""
import logging
from openai import AsyncOpenAI
from src.core.promo_state import PromoState

logger = logging.getLogger(__name__)


class SumarizerAgent:
    """Agent responsável por criar resumos e apresentações de promoções"""
    
    def __init__(self, openai_client: AsyncOpenAI, model: str, prompt_path: str):
        self.client = openai_client
        self.model = model
        
        # Carrega o prompt de sumarização
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt = f.read()
            logger.info(f"Prompt de sumarização carregado: {prompt_path}")
        except Exception as e:
            logger.warning(f"Erro ao carregar prompt: {e}. Usando prompt padrão.")
            self.prompt = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Retorna um prompt padrão caso o arquivo não exista"""
        return """Você é um especialista em criar apresentações profissionais de promoções B2B.

Crie um resumo executivo atraente e profissional da promoção, incluindo:

1. **Título Impactante**: Destaque o nome da promoção
2. **Visão Geral**: Resumo do que é a promoção
3. **Como Funciona**: Mecânica explicada de forma clara
4. **Público-Alvo**: Quem pode participar
5. **Período**: Quando a promoção estará ativa
6. **Benefícios**: O que o cliente ganha
7. **Condições**: Regras importantes
8. **Call-to-Action**: Incentivo para participação

Use formatação markdown para deixar o texto bem organizado e profissional.
Seja persuasivo mas honesto. Destaque os benefícios de forma clara."""
    
    async def summarize(self, state: PromoState) -> str:
        """
        Cria um resumo profissional da promoção
        Se houver múltiplas promoções no metadata, cria resumo de todas
        
        Args:
            state: Estado da promoção a ser resumida
            
        Returns:
            str: Resumo formatado em markdown
        """
        try:
            # Verifica se há múltiplas promoções
            multiple_promos = state.metadata.get('multiple_promotions', [])
            
            if multiple_promos and len(multiple_promos) > 1:
                # MÚLTIPLAS PROMOÇÕES - cria resumo especial
                logger.info(f"Criando resumo para {len(multiple_promos)} promoções")
                
                import json
                promos_json = json.dumps(multiple_promos, ensure_ascii=False, indent=2)
                
                full_prompt = f"""Você recebeu MÚLTIPLAS promoções para resumir.

Crie um resumo profissional listando TODAS as promoções de forma clara e organizada.

Para cada promoção, destaque:
- Título
- Mecânica
- Período
- Público-alvo
- Benefícios principais

Use formatação markdown com emojis. Seja conciso mas informativo.

**PROMOÇÕES:**
{promos_json}"""
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Você é um especialista em criar apresentações profissionais de promoções B2B."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7
                )
                
                summary = response.choices[0].message.content
                summary = f"📊 **{len(multiple_promos)} Promoções Cadastradas**\n\n{summary}"
                logger.info(f"Resumo criado para {len(multiple_promos)} promoções")
                
                return summary
            
            else:
                # PROMOÇÃO ÚNICA - resumo normal
                promo_json = state.to_json()
                full_prompt = f"{self.prompt}\n\n**PROMOÇÃO:**\n{promo_json}"
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Você é um especialista em criar apresentações profissionais de promoções B2B."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7
                )
                
                summary = response.choices[0].message.content
                logger.info(f"Resumo criado para promoção: {state.titulo}")
                
                return summary
            
        except Exception as e:
            logger.error(f"Erro ao criar resumo: {e}")
            return self._create_basic_summary(state)
    
    def _create_basic_summary(self, state: PromoState) -> str:
        """
        Cria um resumo básico sem usar IA (fallback)
        
        Args:
            state: Estado da promoção
            
        Returns:
            str: Resumo básico em markdown
        """
        summary = f"""# 🎯 {state.titulo or 'Promoção'}

## 📋 Informações Gerais

**Mecânica:** {state.mecanica or 'Não especificada'}

**Público-Alvo:** {state.segmentacao or 'Não especificado'}

**Período:** {state.periodo_inicio or 'Início não definido'} até {state.periodo_fim or 'Fim não definido'}

## 📝 Descrição

{state.descricao or 'Descrição não fornecida'}

## ✅ Condições

{state.condicoes or 'Condições não especificadas'}

## 🎁 Recompensas

{state.recompensas or 'Recompensas não especificadas'}
"""
        
        if state.produtos:
            summary += f"\n## 📦 Produtos\n\n"
            for produto in state.produtos:
                summary += f"- {produto}\n"
        
        if state.volume_minimo:
            summary += f"\n**Volume Mínimo:** {state.volume_minimo}"
        
        if state.desconto_percentual:
            summary += f"\n**Desconto:** {state.desconto_percentual}"
        
        return summary
    
    async def create_email_body(self, state: PromoState) -> str:
        """
        Cria o corpo de email HTML para envio da promoção
        
        Args:
            state: Estado da promoção
            
        Returns:
            str: HTML formatado para email
        """
        try:
            # Primeiro cria o resumo
            summary = await self.summarize(state)
            
            # Converte markdown para HTML (simplificado)
            html = self._markdown_to_html(summary)
            
            # Adiciona template de email
            email_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1f3c88 0%, #00a8e8 100%); 
                   color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .highlight {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        h1 {{ margin: 0; }}
        h2 {{ color: #1f3c88; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Nova Promoção</h1>
        </div>
        <div class="content">
            {html}
        </div>
        <div class="footer">
            <p>Gera Sales Ecosystem | PromoAgente</p>
            <p>Este é um email automático gerado pelo PromoAgente</p>
        </div>
    </div>
</body>
</html>
"""
            return email_html
            
        except Exception as e:
            logger.error(f"Erro ao criar email: {e}")
            return f"<html><body><h1>{state.titulo}</h1><p>Erro ao formatar email</p></body></html>"
    
    def _markdown_to_html(self, markdown: str) -> str:
        """
        Converte markdown básico para HTML
        
        Args:
            markdown: Texto em markdown
            
        Returns:
            str: HTML formatado
        """
        # Conversão simplificada - pode ser melhorada com biblioteca markdown
        html = markdown
        
        # Títulos
        html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        html = html.replace('## ', '<h2>').replace('\n', '</h2>\n')
        html = html.replace('### ', '<h3>').replace('\n', '</h3>\n')
        
        # Negrito
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Listas
        html = html.replace('- ', '<li>').replace('\n', '</li>\n')
        
        # Parágrafos
        html = html.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'
        
        return html
