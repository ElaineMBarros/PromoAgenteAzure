"""
Cosmos DB Adapter - Substitui SQLite por Azure Cosmos DB
Compatível com Python 3.11 e Azure Functions
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey, exceptions

logger = logging.getLogger(__name__)


class CosmosDBAdapter:
    """Adapter para Azure Cosmos DB - substitui LocalDatabase"""
    
    def __init__(self):
        """Inicializa conexão com Cosmos DB usando variáveis de ambiente"""
        self.endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        self.key = os.environ.get("COSMOS_DB_KEY")
        self.database_name = "PromoAgente"
        
        if not self.endpoint or not self.key:
            logger.warning("⚠️ Cosmos DB credentials não configuradas. Usando modo local.")
            self.client = None
            self.database = None
            return
        
        try:
            self.client = CosmosClient(self.endpoint, self.key)
            self.database = self.client.get_database_client(self.database_name)
            
            # Containers
            self.sessions_container = self.database.get_container_client("sessions")
            self.messages_container = self.database.get_container_client("messages")
            self.promo_states_container = self.database.get_container_client("promo_states")
            self.promotions_container = self.database.get_container_client("promotions")
            
            logger.info("✅ Cosmos DB conectado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar Cosmos DB: {e}")
            self.client = None
    
    async def initialize(self):
        """Inicialização assíncrona (compatibilidade com código existente)"""
        if not self.client:
            logger.warning("⚠️ Cosmos DB não inicializado")
            return False
        
        logger.info("✅ Cosmos DB pronto para uso")
        return True
    
    # ========== SESSIONS ==========
    
    async def create_session(self, session_id: str, user_agent: str = None) -> bool:
        """Cria uma nova sessão"""
        try:
            session = {
                "id": session_id,
                "partitionKey": "session",
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "user_agent": user_agent or "unknown",
                "ttl": 86400  # 24 horas
            }
            
            self.sessions_container.create_item(session)
            logger.info(f"Session criada: {session_id}")
            return True
            
        except exceptions.CosmosResourceExistsError:
            logger.debug(f"Session já existe: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar session: {e}")
            return False
    
    # ========== MESSAGES ==========
    
    async def save_message(self, session_id: str, user_message: str, ai_response: str) -> bool:
        """Salva uma mensagem no histórico"""
        try:
            message = {
                "id": f"msg_{datetime.utcnow().timestamp()}",
                "session_id": session_id,
                "user_message": user_message,
                "ai_response": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
                "ttl": 2592000  # 30 dias
            }
            
            self.messages_container.create_item(message)
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            return False
    
    async def get_recent_messages(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Busca mensagens recentes de uma sessão"""
        try:
            query = f"""
                SELECT TOP {limit} *
                FROM c
                WHERE c.session_id = @session_id
                ORDER BY c.timestamp DESC
            """
            
            parameters = [{"name": "@session_id", "value": session_id}]
            
            items = list(self.messages_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # Converte para formato esperado pelo código
            messages = []
            for item in reversed(items):  # Ordem cronológica
                if item.get('user_message'):
                    messages.append({
                        "role": "user",
                        "content": item['user_message']
                    })
                if item.get('ai_response'):
                    messages.append({
                        "role": "assistant",
                        "content": item['ai_response'],
                        "timestamp": item.get('timestamp')
                    })
            
            return messages
            
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens: {e}")
            return []
    
    async def get_message_count(self) -> int:
        """Retorna total de mensagens (para health check)"""
        try:
            query = "SELECT VALUE COUNT(1) FROM c"
            result = list(self.messages_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return result[0] if result else 0
            
        except Exception as e:
            logger.warning(f"Erro ao contar mensagens: {e}")
            return 0
    
    # ========== PROMO STATES ==========
    
    async def save_promo_state(self, session_id: str, state_dict: Dict) -> bool:
        """Salva ou atualiza o estado de uma promoção"""
        try:
            promo_state = {
                "id": session_id,
                "partitionKey": "active",
                "promo_id": state_dict.get('promo_id'),
                "status": state_dict.get('status', 'draft'),
                "completion": state_dict.get('completion', 0),
                "data": state_dict,
                "created_at": state_dict.get('created_at', datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat(),
                "ttl": 604800  # 7 dias
            }
            
            self.promo_states_container.upsert_item(promo_state)
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar promo_state: {e}")
            return False
    
    async def get_promo_state(self, session_id: str) -> Optional[Dict]:
        """Recupera o estado de uma promoção"""
        try:
            item = self.promo_states_container.read_item(
                item=session_id,
                partition_key="active"
            )
            return item.get('data') if item else None
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Erro ao recuperar promo_state: {e}")
            return None
    
    async def delete_promo_state(self, session_id: str) -> bool:
        """Remove o estado de uma promoção"""
        try:
            self.promo_states_container.delete_item(
                item=session_id,
                partition_key="active"
            )
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            return True  # Já não existe
        except Exception as e:
            logger.error(f"Erro ao deletar promo_state: {e}")
            return False
    
    async def list_all_promo_states(self) -> List[Dict]:
        """Lista todos os estados de promoções"""
        try:
            query = "SELECT c.data FROM c"
            items = list(self.promo_states_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return [item['data'] for item in items]
            
        except Exception as e:
            logger.error(f"Erro ao listar promo_states: {e}")
            return []
    
    # ========== PROMOTIONS (FINALIZADAS) ==========
    
    async def save_promotion(self, state_dict: Dict) -> bool:
        """Salva uma promoção finalizada"""
        try:
            # Partition key baseado em ano-mês para otimizar queries
            periodo_inicio = state_dict.get('periodo_inicio', '')
            partition_key = self._extract_year_month(periodo_inicio)
            
            promotion = {
                "id": state_dict.get('promo_id'),
                "partitionKey": partition_key,
                **state_dict,  # Todos os campos do state_dict
                "created_at": state_dict.get('created_at', datetime.utcnow().isoformat()),
                "sent_at": datetime.utcnow().isoformat()
            }
            
            # Remove campos desnecessários
            promotion.pop('completion', None)
            promotion.pop('metadata', None)
            
            self.promotions_container.create_item(promotion)
            logger.info(f"Promoção salva: {state_dict.get('promo_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar promotion: {e}")
            return False
    
    async def get_promotions(self, limit: int = 50) -> List[Dict]:
        """Lista promoções finalizadas"""
        try:
            query = f"""
                SELECT TOP {limit} *
                FROM c
                ORDER BY c.created_at DESC
            """
            
            items = list(self.promotions_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items
            
        except Exception as e:
            logger.error(f"Erro ao listar promotions: {e}")
            return []
    
    async def get_promotion_by_id(self, promo_id: str) -> Optional[Dict]:
        """Busca uma promoção por ID"""
        try:
            # Como não sabemos o partition key, fazemos query cross-partition
            query = "SELECT * FROM c WHERE c.id = @promo_id"
            parameters = [{"name": "@promo_id", "value": promo_id}]
            
            items = list(self.promotions_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar promotion: {e}")
            return None
    
    # ========== HELPERS ==========
    
    def _extract_year_month(self, date_str: str) -> str:
        """Extrai ano-mês de uma data para partition key"""
        try:
            # Tenta parsear DD/MM/YYYY ou YYYY-MM-DD
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1]}"  # YYYY-MM
            elif '-' in date_str:
                return date_str[:7]  # YYYY-MM
            
            # Fallback: ano-mês atual
            return datetime.utcnow().strftime("%Y-%m")
            
        except:
            return datetime.utcnow().strftime("%Y-%m")


# Instância global (singleton)
cosmos_adapter = CosmosDBAdapter()
