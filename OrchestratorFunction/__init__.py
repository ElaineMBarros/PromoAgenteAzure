"""
OrchestratorFunction - Azure Function coordenadora
Gerencia o fluxo completo de criação de promoções
Coordena ExtractorFunction, ValidatorFunction e SumarizerFunction
"""
import logging
import json
import os
import azure.functions as func
from typing import Dict, Optional
import httpx
from datetime import datetime
import uuid
from openai import AsyncAzureOpenAI
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import do prompt loader
try:
    from shared.utils.prompt_loader import get_persona_prompt
    PROMPT_LOADER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Prompt loader não disponível: {e}")
    PROMPT_LOADER_AVAILABLE = False

# Import do cosmos adapter
try:
    from shared.adapters.cosmos_adapter import cosmos_adapter
    COSMOS_ADAPTER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Cosmos adapter não disponível: {e}")
    COSMOS_ADAPTER_AVAILABLE = False
    cosmos_adapter = None

logger = logging.getLogger(__name__)

# Configuração
# Detecta automaticamente se está no Azure ou local
FUNCTION_APP_URL = os.environ.get("FUNCTION_APP_URL")
if not FUNCTION_APP_URL:
    # Se WEBSITE_HOSTNAME existe, está no Azure
    website_hostname = os.environ.get("WEBSITE_HOSTNAME")
    if website_hostname:
        FUNCTION_APP_URL = f"https://{website_hostname}"
        logger.info(f"🌐 Rodando no Azure: {FUNCTION_APP_URL}")
    else:
        FUNCTION_APP_URL = "http://localhost:7071"
        logger.info(f"💻 Rodando localmente: {FUNCTION_APP_URL}")

COSMOS_CONNECTION = os.environ.get("COSMOS_CONNECTION_STRING")

# Configuração Azure OpenAI
AZURE_OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("OPENAI_API_ENDPOINT", "https://eastus.api.cognitive.microsoft.com/")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"


class PromoOrchestrator:
    """Orquestrador do fluxo de promoções"""
    
    def __init__(self):
        self.extractor_url = f"{FUNCTION_APP_URL}/api/extract"
        self.validator_url = f"{FUNCTION_APP_URL}/api/validate"
        self.summarizer_url = f"{FUNCTION_APP_URL}/api/summarize"
        self.export_url = f"{FUNCTION_APP_URL}/api/export"
    
    def _validate_date_immediately(self, promo_data: Dict) -> Optional[str]:
        """
        Valida data IMEDIATAMENTE após extração
        Retorna mensagem de erro se data inválida, None se OK
        """
        periodo_inicio = promo_data.get("periodo_inicio")
        if not periodo_inicio:
            return None
        
        try:
            from datetime import datetime
            hoje = datetime.now()
            
            # Tenta parsear diferentes formatos
            data_inicio = None
            
            # Formato DD/MM/YYYY
            if len(periodo_inicio) == 10 and '/' in periodo_inicio:
                try:
                    data_inicio = datetime.strptime(periodo_inicio, "%d/%m/%Y")
                except:
                    pass
            
            # Formato DD/MM (assume ano atual)
            if not data_inicio and len(periodo_inicio) == 5 and '/' in periodo_inicio:
                try:
                    dia, mes = periodo_inicio.split('/')
                    data_inicio = datetime(hoje.year, int(mes), int(dia))
                except:
                    pass
            
            # Se conseguiu parsear, valida
            if data_inicio:
                # Data no passado
                if data_inicio.date() < hoje.date():
                    # Mesmo mês mas dia passou
                    if data_inicio.month == hoje.month and data_inicio.year == hoje.year:
                        return f"""⚠️ **Data inválida detectada!**

A data de início ({periodo_inicio}) já passou. Estamos em {hoje.strftime('%d/%m/%Y')}.

Por favor, informe uma nova data a partir de hoje ou posterior."""
                    
                    # Mês passado - sugere ano seguinte
                    elif data_inicio.month < hoje.month and data_inicio.year == hoje.year:
                        nova_data = periodo_inicio.replace(str(hoje.year), str(hoje.year + 1))
                        return f"""💡 **Ajuste de data sugerido**

Detectei que a data ({periodo_inicio}) está no passado.

Sugiro ajustar para **{nova_data}** (ano seguinte). Confirma essa mudança?"""
                    
                    # Ano passado
                    elif data_inicio.year < hoje.year:
                        nova_data = periodo_inicio.replace(str(data_inicio.year), str(hoje.year + 1))
                        return f"""💡 **Ajuste de data sugerido**

Detectei que a data ({periodo_inicio}) está no ano passado.

Sugiro ajustar para **{nova_data}**. Confirma?"""
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao validar data: {e}")
            return None
    
    async def _generate_response_with_persona(
        self,
        user_message: str,
        promo_data: Dict,
        status: str,
        history: list
    ) -> str:
        """
        Gera resposta usando Azure OpenAI com prompt persona
        """
        if not AZURE_OPENAI_KEY:
            # Fallback para resposta básica
            return "Olá! Vamos criar uma promoção. Me conte sobre ela!"
        
        try:
            # Carrega prompt persona
            if PROMPT_LOADER_AVAILABLE:
                persona_prompt = get_persona_prompt()
            else:
                persona_prompt = "Você é um assistente amigável que ajuda a criar promoções."
            
            # Monta contexto
            context = f"""
Estado atual da promoção:
- Dados coletados: {json.dumps(promo_data, ensure_ascii=False)}
- Status: {status}
- É primeira mensagem: {len(history) <= 1}
"""
            
            # Cliente Azure OpenAI
            client = AsyncAzureOpenAI(
                api_key=AZURE_OPENAI_KEY,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT
            )
            
            # Gera resposta
            response = await client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": persona_prompt},
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com persona: {e}")
            return "Olá! Vamos criar uma promoção. Me conte sobre ela!"
    
    async def process_message(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        current_state: Optional[Dict] = None
    ) -> Dict:
        """
        Processa mensagem do usuário e orquestra o fluxo
        
        Args:
            message: Mensagem do usuário
            session_id: ID da sessão (opcional)
            current_state: Estado atual da promoção (opcional)
            
        Returns:
            Dict com resposta e dados atualizados
        """
        # Gera session_id se não fornecido
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Nova sessão criada: {session_id}")
        
        # Estado inicial
        if not current_state:
            current_state = {
                "session_id": session_id,
                "status": "draft",
                "created_at": datetime.utcnow().isoformat(),
                "data": {},
                "history": []
            }
        
        # Adiciona mensagem ao histórico
        current_state["history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            # Detecta comandos especiais
            message_lower = message.lower().strip()
            
            # Comando: gerar excel
            if "gerar excel" in message_lower or "gerar planilha" in message_lower:
                logger.info("📊 Comando detectado: gerar excel")
                if current_state.get("status") == "ready" and current_state.get("data"):
                    export_result = await self._call_export(current_state["data"])
                    if export_result.get("success"):
                        # Armazena o base64 no estado para o frontend processar
                        current_state["data"]["excel_base64"] = export_result.get("excel_base64")
                        current_state["data"]["excel_filename"] = export_result.get("filename")
                        
                        response = f"""✅ **Excel gerado com sucesso!**

📄 Arquivo: `{export_result.get('filename')}`

💡 **O download iniciará automaticamente!**

Deseja fazer algo mais com esta promoção?"""
                    else:
                        response = f"⚠️ Erro ao gerar Excel: {export_result.get('error', 'Erro desconhecido')}"
                else:
                    response = "⚠️ A promoção precisa estar completa e validada antes de gerar o Excel. Complete as informações faltantes primeiro."
                
                # Adiciona ao histórico e retorna
                current_state["history"].append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                current_state["updated_at"] = datetime.utcnow().isoformat()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "response": response,
                    "state": current_state,
                    "status": current_state["status"]
                }
            
            # 🔒 PROTEÇÃO: Se já está "ready" e mensagem é confirmação, mantém status
            confirmacao_palavras = ["confirmo", "confirma", "ok", "está bom", "perfeito", "certo", "sim", "correto"]
            is_confirmacao = any(palavra in message_lower for palavra in confirmacao_palavras)
            
            if current_state.get("status") == "ready" and is_confirmacao:
                logger.info("✅ Status 'ready' + confirmação detectada - mantendo estado")
                
                response = f"""✅ **Ótimo! Promoção confirmada e pronta!**

{current_state['data'].get('summary', '')}

**O que deseja fazer?**
- Digite "gerar excel" para exportar a planilha
- Continue refinando os detalhes se necessário"""
                
                current_state["history"].append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                current_state["updated_at"] = datetime.utcnow().isoformat()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "response": response,
                    "state": current_state,
                    "status": "ready"
                }
            
            # PASSO 1: Extrai informações
            logger.info("🔍 PASSO 1: Extraindo informações")
            extract_result = await self._call_extractor(message, current_state.get("data"))
            
            if not extract_result.get("success"):
                error_msg = extract_result.get("error", "Erro desconhecido na extração")
                logger.error(f"❌ Erro na extração: {error_msg}")
                return {
                    "success": False,
                    "session_id": session_id,
                    "response": f"Desculpe, ocorreu um erro ao processar sua mensagem: {error_msg}",
                    "state": current_state
                }
            
            # Atualiza dados extraídos
            extracted_data = extract_result.get("data", {})
            is_multiple = extract_result.get("is_multiple", False)
            
            if is_multiple:
                logger.info(f"📝 Múltiplas promoções detectadas: {len(extracted_data)}")
                # Para múltiplas, armazena no metadata
                current_state["data"]["multiple_promotions"] = extracted_data
                # Merge inteligente da primeira promoção
                for key, value in extracted_data[0].items():
                    if value is not None and value != "":
                        current_state["data"][key] = value
            else:
                # MERGE INTELIGENTE: apenas atualiza campos com valores reais
                # Preserva dados anteriores se o novo valor for None ou vazio
                for key, value in extracted_data.items():
                    if value is not None and value != "":
                        # Se é lista vazia, não atualiza
                        if isinstance(value, list) and len(value) == 0:
                            continue
                        current_state["data"][key] = value
                        logger.info(f"📝 Atualizado: {key} = {value}")
            
            logger.info(f"✅ Extração concluída - {len(current_state['data'])} campos no estado")
            
            # ✅ VALIDAÇÃO IMEDIATA DE DATA
            promo_data = current_state["data"]
            date_error = self._validate_date_immediately(promo_data)
            if date_error:
                logger.warning(f"⚠️ Data inválida detectada imediatamente")
                current_state["status"] = "needs_review"
                
                # Retorna erro de data IMEDIATAMENTE
                current_state["history"].append({
                    "role": "assistant",
                    "content": date_error,
                    "timestamp": datetime.utcnow().isoformat()
                })
                current_state["updated_at"] = datetime.utcnow().isoformat()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "response": date_error,
                    "state": current_state,
                    "status": "needs_review"
                }
            
            # PASSO 2: Decide próximo estado (SE DATA OK)
            
            # Verifica se tem informações suficientes
            # Campos obrigatórios definidos pelo usuário
            campos_criticos = [
                "titulo", "mecanica", "descricao", 
                "periodo_inicio", "periodo_fim",
                "condicoes", "recompensas", "produtos", "segmentacao"
            ]
            # ✅ CORREÇÃO: Verifica campos no ESTADO COMPLETO, não só na mensagem atual
            campos_preenchidos = [c for c in campos_criticos if promo_data.get(c)]
            campos_faltando = [c for c in campos_criticos if not promo_data.get(c)]
            
            # Só valida se tiver TODOS os campos críticos (9)
            if len(campos_preenchidos) == 9:
                # Tem TODOS os campos críticos -> valida
                logger.info("✅ PASSO 2: Validando promoção")
                
                # IMPORTANTE: Envia apenas campos relevantes para validação
                # Remove campos None e metadatos para não confundir a GPT
                promo_data_clean = {
                    k: v for k, v in promo_data.items() 
                    if v is not None and k not in ['erro', 'summary', 'excel_base64', 'excel_filename', 'multiple_promotions']
                }
                
                validation_result = await self._call_validator(promo_data_clean)
                
                if validation_result.get("is_valid"):
                    # Válida -> cria resumo
                    logger.info("✅ PASSO 3: Criando resumo")
                    
                    summary_result = await self._call_summarizer(promo_data)
                    current_state["data"]["summary"] = summary_result.get("summary", "")
                    current_state["status"] = "ready"
                    
                    # ✅ SALVA PROMOÇÃO NO COSMOS DB
                    if COSMOS_ADAPTER_AVAILABLE and cosmos_adapter and cosmos_adapter.client:
                      # ✅ SALVA PROMOÇÃO NO COSMOS DB
logger.info("=" * 70)
logger.info("🔍 DEBUG SALVAMENTO:")
logger.info(f"   COSMOS_ADAPTER_AVAILABLE: {COSMOS_ADAPTER_AVAILABLE}")
logger.info(f"   cosmos_adapter: {cosmos_adapter}")
logger.info(f"   cosmos_adapter.client: {cosmos_adapter.client if cosmos_adapter else 'N/A'}")
logger.info("=" * 70)

if COSMOS_ADAPTER_AVAILABLE and cosmos_adapter and cosmos_adapter.client:
    try:
        if not promo_data.get("promo_id"):
            promo_data["promo_id"] = f"promo_{session_id}_{int(datetime.utcnow().timestamp())}"
        
        logger.info(f"💾 Tentando salvar: {promo_data.get('titulo', 'sem título')}")
        await cosmos_adapter.save_promotion(promo_data)
        logger.info(f"✅ Promoção salva no Cosmos DB")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar: {e}")
        import traceback
        logger.error(traceback.format_exc())
else:
    logger.warning("=" * 70)
    logger.warning("⚠️ COSMOS DB NÃO DISPONÍVEL")
    logger.warning(f"   COSMOS_ADAPTER_AVAILABLE = {COSMOS_ADAPTER_AVAILABLE}")
    if not cosmos_adapter:
        logger.warning("   cosmos_adapter = None")
    elif not cosmos_adapter.client:
        logger.warning("   cosmos_adapter.client = None")
    logger.warning("=" * 70)


{summary_result.get('summary', '')}

**Opções:**
- Digite "gerar excel" para exportar a planilha
- Continue refinando os detalhes se necessário"""
                    
                else:
                    # Inválida -> informa problemas
                    issues = validation_result.get("issues", [])
                    current_state["status"] = "needs_review"
                    
                    # ✅ FALLBACK: Se issues está vazio mas validação falhou, usa feedback
                    if not issues:
                        feedback_text = validation_result.get('feedback', 'Validação reprovou mas não especificou os problemas')
                        if feedback_text:
                            issues = [feedback_text]
                        else:
                            issues = ["Validação reprovou - verifique os dados da promoção"]
                        logger.warning(f"⚠️ Validator retornou issues vazio, usando fallback")
                    
                    response = f"""⚠️ **Validação encontrou alguns problemas:**

{validation_result.get('feedback', '')}

**Problemas:**
{chr(10).join(['- ' + i for i in issues])}

Por favor, forneça as informações faltantes ou corrija os problemas."""
            else:
                # Falta informação -> pede mais
                current_state["status"] = "gathering"
                
                # Usa persona APENAS se for REALMENTE a primeira mensagem
                # (histórico tem apenas 1 item = a mensagem atual do usuário)
                user_messages_count = len([h for h in current_state["history"] if h.get("role") == "user"])
                is_first_message = user_messages_count == 1
                
                # 🔍 LOGS DE DEBUG
                logger.info(f"🔍 DEBUG - Total mensagens user: {user_messages_count}")
                logger.info(f"🔍 DEBUG - is_first_message: {is_first_message}")
                logger.info(f"🔍 DEBUG - campos_preenchidos: {len(campos_preenchidos)}")
                logger.info(f"🔍 DEBUG - campos_faltando: {len(campos_faltando)}")
                
                # ✅ CORREÇÃO: SEMPRE mostra dados se tem algo no estado
                if campos_preenchidos:
                    # TEM DADOS NO ESTADO -> Mostra progresso
                    logger.info(f"📝 Mostrando {len(campos_preenchidos)} campos preenchidos")
                    
                    # Mostra dados coletados até agora
                    dados_extraidos = []
                    if promo_data.get("titulo"):
                        dados_extraidos.append(f"✅ Título: {promo_data['titulo']}")
                    if promo_data.get("mecanica"):
                        dados_extraidos.append(f"✅ Mecânica: {promo_data['mecanica']}")
                    if promo_data.get("descricao"):
                        dados_extraidos.append(f"✅ Descrição: {promo_data['descricao']}")
                    if promo_data.get("desconto_percentual"):
                        dados_extraidos.append(f"✅ Desconto: {promo_data['desconto_percentual']}%")
                    if promo_data.get("periodo_inicio"):
                        dados_extraidos.append(f"✅ Início: {promo_data['periodo_inicio']}")
                    if promo_data.get("periodo_fim"):
                        dados_extraidos.append(f"✅ Fim: {promo_data['periodo_fim']}")
                    if promo_data.get("condicoes"):
                        dados_extraidos.append(f"✅ Condições: {promo_data['condicoes']}")
                    if promo_data.get("recompensas"):
                        dados_extraidos.append(f"✅ Recompensas: {promo_data['recompensas']}")
                    if promo_data.get("produtos"):
                        produtos_str = promo_data['produtos'] if isinstance(promo_data['produtos'], str) else ', '.join(promo_data['produtos'])
                        dados_extraidos.append(f"✅ Produtos: {produtos_str}")
                    if promo_data.get("segmentacao"):
                        dados_extraidos.append(f"✅ Segmentação: {promo_data['segmentacao']}")
                    
                    if len(campos_faltando) > 0:
                        response = f"""📝 **Dados coletados até agora:**

{chr(10).join(dados_extraidos)}

⚠️ **Ainda faltam {len(campos_faltando)} campos:** {', '.join(campos_faltando)}

Por favor, complete as informações faltantes."""
                    else:
                        response = f"""📝 **Todos os dados coletados!**

{chr(10).join(dados_extraidos)}

Validando promoção..."""
                
                elif is_first_message:
                    # PRIMEIRA MENSAGEM SEM DADOS -> Boas-vindas
                    logger.info("🤖 Gerando boas-vindas com persona (primeira mensagem sem dados)")
                    response = await self._generate_response_with_persona(
                        message,
                        promo_data,
                        "gathering",
                        current_state["history"]
                    )
                
                else:
                    # NÃO É PRIMEIRA MENSAGEM E NÃO TEM DADOS -> Pede clarificação
                    logger.info("⚠️ Segunda+ mensagem sem dados extraídos - pedindo clarificação")
                    response = """Não consegui identificar dados da promoção nessa mensagem. 

Por favor, me passe informações como:
- 📌 **Título** ou nome da promoção
- 🎯 **Tipo/Mecânica** (progressiva, combo, desconto, etc)
- 📅 **Período** de validade (início e fim)
- ✅ **Condições** (quantidades mínimas, produtos, etc)
- 🎁 **Recompensas** (descontos, brindes, etc)
- 👥 **Público-alvo** ou segmentação

Pode descrever de forma natural ou estruturada!"""
            
            # Adiciona resposta ao histórico
            current_state["history"].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            current_state["updated_at"] = datetime.utcnow().isoformat()
            
            return {
                "success": True,
                "session_id": session_id,
                "response": response,
                "state": current_state,
                "status": current_state["status"]
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no orquestrador: {str(e)}")
            return {
                "success": False,
                "session_id": session_id,
                "response": f"Desculpe, ocorreu um erro: {str(e)}",
                "state": current_state
            }
    
    async def _call_extractor(self, text: str, current_state: Optional[Dict] = None) -> Dict:
        """Chama ExtractorFunction"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.extractor_url,
                    json={
                        "text": text,
                        "current_state": current_state
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Erro ao chamar Extractor: {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_validator(self, promo_data: Dict) -> Dict:
        """Chama ValidatorFunction"""
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.validator_url,
                    json={"promo_data": promo_data}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Erro ao chamar Validator: {e}")
            return {"success": False, "is_valid": False, "error": str(e)}
    
    async def _call_summarizer(self, promo_data: Dict, output_type: str = "summary") -> Dict:
        """Chama SumarizerFunction"""
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.summarizer_url,
                    json={
                        "promo_data": promo_data,
                        "type": output_type
                    }
                )
                response.raise_for_status()
                
                if output_type == "email":
                    return {"email_html": response.text}
                else:
                    return response.json()
        except Exception as e:
            logger.error(f"Erro ao chamar Summarizer: {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_export(self, promo_data: Dict) -> Dict:
        """Chama ExportFunction para gerar Excel"""
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.export_url,
                    json={
                        "promo_data": promo_data,
                        "format": "excel"
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Erro ao chamar Export: {e}")
            return {"success": False, "error": str(e)}


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function principal - Orchestrator
    
    POST /api/orchestrator
    
    Request Body:
    {
        "message": "Texto do usuário",
        "session_id": "uuid" (opcional),
        "current_state": {} (opcional)
    }
    
    Response:
    {
        "success": true,
        "session_id": "uuid",
        "response": "Resposta para o usuário",
        "state": {estado completo},
        "status": "draft|gathering|ready|needs_review"
    }
    """
    logger.info('🎯 OrchestratorFunction: Processando requisição')
    
    try:
        # Parse request
        req_body = req.get_json()
        message = req_body.get('message')
        session_id = req_body.get('session_id')
        current_state = req_body.get('current_state')
        
        if not message:
            logger.warning("⚠️ Campo 'message' não fornecido")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": "Campo 'message' é obrigatório"
                }),
                mimetype="application/json",
                status_code=400
            )
        
        logger.info(f"💬 Mensagem recebida: {message[:100]}...")
        if session_id:
            logger.info(f"📋 Sessão: {session_id}")
        
        # Processa mensagem
        orchestrator = PromoOrchestrator()
        result = await orchestrator.process_message(message, session_id, current_state)
        
        # Log resultado
        if result.get('success'):
            logger.info(f"✅ Processamento concluído: {result.get('status')}")
        else:
            logger.error(f"❌ Processamento falhou")
        
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if result.get('success') else 500
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
        logger.error(f"❌ Erro na OrchestratorFunction: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
