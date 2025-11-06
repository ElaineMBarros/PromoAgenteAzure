"""
ExtractorAgent - Extrai informações de promoções de texto não estruturado
"""
import json
import logging
from typing import Dict
from openai import AsyncOpenAI
from src.core.promo_state import PromoState

logger = logging.getLogger(__name__)


class ExtractorAgent:
    """Agent responsável por extrair informações estruturadas de promoções"""
    
    def __init__(self, openai_client: AsyncOpenAI, model: str, prompt_path: str):
        self.client = openai_client
        self.model = model
        
        # Carrega o prompt de extração
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt = f.read()
            logger.info(f"Prompt de extração carregado: {prompt_path}")
        except Exception as e:
            logger.warning(f"Erro ao carregar prompt: {e}. Usando prompt padrão.")
            self.prompt = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Retorna um prompt padrão caso o arquivo não exista"""
        return """Você é um assistente especializado em extrair informações de promoções B2B do varejo.

Extraia as seguintes informações do texto fornecido e retorne em formato JSON:

{
  "titulo": "Título da promoção (se mencionado)",
  "mecanica": "Tipo de mecânica (progressiva, casada, pontos, relâmpago, escalonada, VIP)",
  "descricao": "Descrição de como funciona",
  "segmentacao": "Público-alvo ou segmento de clientes",
  "periodo_inicio": "Data de início (formato: YYYY-MM-DD ou descrição)",
  "periodo_fim": "Data de fim (formato: YYYY-MM-DD ou descrição)",
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
- Mantenha o contexto B2B de varejo"""
    
    async def extract(self, text: str, state: PromoState) -> PromoState:
        """
        Extrai informações do texto e atualiza o PromoState
        Detecta se há múltiplas promoções (array) e armazena no metadata
        
        Args:
            text: Texto com informações da promoção
            state: Estado atual da promoção
            
        Returns:
            PromoState atualizado com novas informações
        """
        try:
            # Adiciona data atual para interpretar datas relativas
            from datetime import datetime
            current_date = datetime.now().strftime("%d/%m/%Y")
            
            # Substitui o placeholder {current_date} no prompt
            prompt_with_date = self.prompt.replace("{current_date}", current_date)
            
            # Prepara o prompt completo
            full_prompt = f"{prompt_with_date}\n\n**TEXTO DO USUÁRIO:**\n{text}"
            
            # Chama a API do OpenAI (SEM response_format para aceitar arrays)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em extrair informações de promoções B2B. Retorne JSON puro (objeto único OU array de objetos se múltiplas promoções)."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extrai o JSON da resposta
            content = response.choices[0].message.content
            
            # Remove possíveis marcadores de código markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            extracted_data = json.loads(content)
            
            logger.info(f"Dados extraídos: {json.dumps(extracted_data, ensure_ascii=False)[:500]}...")
            
            # DETECTA SE É ARRAY (múltiplas promoções)
            if isinstance(extracted_data, list) and len(extracted_data) > 0:
                logger.info(f"🔍 Detectadas {len(extracted_data)} promoções múltiplas!")
                
                # Armazena TODAS no metadata
                state.metadata['multiple_promotions'] = extracted_data
                
                # Preenche o state principal com a PRIMEIRA promoção
                first_promo = extracted_data[0]
                for field, value in first_promo.items():
                    if value and value != "null" and hasattr(state, field):
                        if isinstance(value, str):
                            setattr(state, field, value.strip())
                        else:
                            setattr(state, field, value)
                        logger.debug(f"Campo '{field}' atualizado: {value}")
                
                logger.info(f"✅ Múltiplas promoções armazenadas no metadata. State principal preenchido com primeira promoção.")
            
            else:
                # PROMOÇÃO ÚNICA (objeto JSON normal)
                for field, value in extracted_data.items():
                    if value and value != "null" and hasattr(state, field):
                        if isinstance(value, str):
                            setattr(state, field, value.strip())
                        else:
                            setattr(state, field, value)
                        logger.debug(f"Campo '{field}' atualizado: {value}")
            
            return state
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            logger.error(f"Conteúdo recebido: {content[:500]}")
            return state
        except Exception as e:
            logger.error(f"Erro ao extrair informações: {e}")
            return state
    
    async def extract_incremental(self, text: str, state: PromoState, conversation_history: list = None) -> tuple[PromoState, list]:
        """
        Extrai informações e retorna também a lista de campos atualizados
        
        Args:
            text: Texto do usuário
            state: Estado atual
            conversation_history: Histórico das últimas conversas (opcional)
        
        Returns:
            tuple: (PromoState atualizado, lista de campos modificados)
        """
        # Se tem histórico, adiciona contexto ao prompt
        if conversation_history and len(conversation_history) > 0:
            context_summary = self._build_context_from_history(conversation_history, state)
            enhanced_text = f"{context_summary}\n\n**NOVA MENSAGEM DO USUÁRIO:**\n{text}"
        else:
            enhanced_text = text
        
        original_dict = state.to_dict()
        updated_state = await self.extract(enhanced_text, state)
        updated_dict = updated_state.to_dict()
        
        # Identifica campos que foram atualizados
        updated_fields = []
        for key in original_dict.keys():
            if original_dict[key] != updated_dict[key]:
                updated_fields.append(key)
        
        return updated_state, updated_fields
    
    def _build_context_from_history(self, history: list, state: PromoState) -> str:
        """
        Constrói um resumo do contexto baseado no histórico de conversas
        
        Args:
            history: Lista de mensagens anteriores
            state: Estado atual da promoção
            
        Returns:
            str: Resumo do contexto
        """
        context_parts = ["**CONTEXTO DA CONVERSA:**"]
        
        # Resume o que já foi coletado
        if state.titulo:
            context_parts.append(f"- Título já definido: {state.titulo}")
        if state.mecanica:
            context_parts.append(f"- Mecânica já definida: {state.mecanica}")
        if state.segmentacao:
            context_parts.append(f"- Público já definido: {state.segmentacao}")
        if state.periodo_inicio or state.periodo_fim:
            context_parts.append(f"- Período já discutido: {state.periodo_inicio} até {state.periodo_fim}")
        
        # Adiciona últimas 3 mensagens do usuário para contexto
        user_messages = [msg for msg in history if msg and isinstance(msg, dict) and msg.get('role') == 'user'][-3:]
        if user_messages:
            context_parts.append("\n**Mensagens recentes do usuário:**")
            for i, msg in enumerate(user_messages, 1):
                content = msg.get('content', '')[:100]
                context_parts.append(f"{i}. {content}...")
        
        return "\n".join(context_parts)
