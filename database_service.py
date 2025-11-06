"""
Serviço de banco de dados para gerenciar promoções no Azure Cosmos DB
"""
import os
import logging
from typing import List, Optional
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from models import Promocao


class PromocaoService:
    """Serviço para gerenciar promoções no Cosmos DB"""

    def __init__(self):
        """Inicializa a conexão com o Cosmos DB"""
        connection_string = os.getenv("COSMOS_DB_CONNECTION_STRING")
        database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "PromocoesDB")
        container_name = os.getenv("COSMOS_DB_CONTAINER_NAME", "Promocoes")

        self.logger = logging.getLogger(__name__)
        
        if not connection_string:
            self.logger.warning("COSMOS_DB_CONNECTION_STRING não configurada. Usando modo simulado.")
            self.client = None
            self.database = None
            self.container = None
            return

        try:
            self.client = CosmosClient.from_connection_string(connection_string)
            self.database = self.client.get_database_client(database_name)
            self.container = self.database.get_container_client(container_name)
            self.logger.info(f"Conectado ao Cosmos DB: {database_name}/{container_name}")
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao Cosmos DB: {str(e)}")
            self.client = None
            self.database = None
            self.container = None

    def criar_promocao(self, promocao: Promocao) -> Promocao:
        """Cria uma nova promoção"""
        if not self.container:
            raise Exception("Cosmos DB não configurado")

        try:
            promocao_dict = promocao.model_dump(mode='json')
            # Cosmos DB requer o campo 'id' como string
            promocao_dict['id'] = str(promocao_dict['id'])
            
            self.container.create_item(body=promocao_dict)
            self.logger.info(f"Promoção criada com ID: {promocao.id}")
            return promocao
        except exceptions.CosmosResourceExistsError:
            raise ValueError(f"Promoção com ID {promocao.id} já existe")
        except Exception as e:
            self.logger.error(f"Erro ao criar promoção: {str(e)}")
            raise

    def obter_promocao(self, promocao_id: str) -> Optional[Promocao]:
        """Obtém uma promoção por ID"""
        if not self.container:
            raise Exception("Cosmos DB não configurado")

        try:
            item = self.container.read_item(item=promocao_id, partition_key=promocao_id)
            return Promocao(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter promoção: {str(e)}")
            raise

    def listar_promocoes(self, ativas_apenas: bool = False) -> List[Promocao]:
        """Lista todas as promoções"""
        if not self.container:
            raise Exception("Cosmos DB não configurado")

        try:
            query = "SELECT * FROM c"
            if ativas_apenas:
                query += " WHERE c.ativa = true"
            
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return [Promocao(**item) for item in items]
        except Exception as e:
            self.logger.error(f"Erro ao listar promoções: {str(e)}")
            raise

    def atualizar_promocao(self, promocao_id: str, promocao: Promocao) -> Promocao:
        """Atualiza uma promoção existente"""
        if not self.container:
            raise Exception("Cosmos DB não configurado")

        try:
            # Verifica se a promoção existe
            existing = self.obter_promocao(promocao_id)
            if not existing:
                raise ValueError(f"Promoção com ID {promocao_id} não encontrada")

            promocao_dict = promocao.model_dump(mode='json')
            promocao_dict['id'] = promocao_id
            
            self.container.upsert_item(body=promocao_dict)
            self.logger.info(f"Promoção atualizada: {promocao_id}")
            return promocao
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Erro ao atualizar promoção: {str(e)}")
            raise

    def deletar_promocao(self, promocao_id: str) -> bool:
        """Deleta uma promoção"""
        if not self.container:
            raise Exception("Cosmos DB não configurado")

        try:
            self.container.delete_item(item=promocao_id, partition_key=promocao_id)
            self.logger.info(f"Promoção deletada: {promocao_id}")
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Erro ao deletar promoção: {str(e)}")
            raise

    def desativar_promocao(self, promocao_id: str) -> Optional[Promocao]:
        """Desativa uma promoção (soft delete)"""
        promocao = self.obter_promocao(promocao_id)
        if not promocao:
            return None
        
        promocao.ativa = False
        return self.atualizar_promocao(promocao_id, promocao)
