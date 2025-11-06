"""
Azure Function para gerenciamento de promoções
Suporta operações CRUD via HTTP
"""
import json
import logging
import azure.functions as func
from datetime import datetime, timezone
from typing import Optional

# Importações dos módulos locais
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Promocao
from database_service import PromocaoService


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Função principal para gerenciar promoções
    
    Rotas:
    - GET /api/promocoes - Lista todas as promoções
    - GET /api/promocoes/{id} - Obtém uma promoção específica
    - POST /api/promocoes - Cria uma nova promoção
    - PUT /api/promocoes/{id} - Atualiza uma promoção
    - DELETE /api/promocoes/{id} - Deleta uma promoção
    """
    logging.info('Processando requisição para promoções')
    
    # Inicializa o serviço
    service = PromocaoService()
    
    # Obtém o ID da rota (se fornecido)
    promocao_id = req.route_params.get('id')
    
    # Obtém o método HTTP
    method = req.method
    
    try:
        if method == 'GET':
            return handle_get(service, promocao_id, req)
        elif method == 'POST':
            return handle_post(service, req)
        elif method == 'PUT':
            return handle_put(service, promocao_id, req)
        elif method == 'DELETE':
            return handle_delete(service, promocao_id)
        else:
            return func.HttpResponse(
                json.dumps({"erro": "Método não suportado"}),
                status_code=405,
                mimetype="application/json"
            )
    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"erro": str(e)}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Erro ao processar requisição: {str(e)}")
        return func.HttpResponse(
            json.dumps({"erro": "Erro interno do servidor"}),
            status_code=500,
            mimetype="application/json"
        )


def handle_get(service: PromocaoService, promocao_id: Optional[str], req: func.HttpRequest) -> func.HttpResponse:
    """Trata requisições GET"""
    if promocao_id:
        # Obter promoção específica
        promocao = service.obter_promocao(promocao_id)
        if not promocao:
            return func.HttpResponse(
                json.dumps({"erro": "Promoção não encontrada"}),
                status_code=404,
                mimetype="application/json"
            )
        return func.HttpResponse(
            promocao.model_dump_json(),
            status_code=200,
            mimetype="application/json"
        )
    else:
        # Listar promoções
        ativas_apenas = req.params.get('ativas', 'false').lower() == 'true'
        promocoes = service.listar_promocoes(ativas_apenas=ativas_apenas)
        promocoes_json = [p.model_dump(mode='json') for p in promocoes]
        return func.HttpResponse(
            json.dumps(promocoes_json, default=str),
            status_code=200,
            mimetype="application/json"
        )


def handle_post(service: PromocaoService, req: func.HttpRequest) -> func.HttpResponse:
    """Trata requisições POST (criar promoção)"""
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"erro": "JSON inválido"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        # Converte strings de data para datetime se necessário
        if isinstance(req_body.get('data_inicio'), str):
            req_body['data_inicio'] = datetime.fromisoformat(req_body['data_inicio'].replace('Z', '+00:00'))
        if isinstance(req_body.get('data_fim'), str):
            req_body['data_fim'] = datetime.fromisoformat(req_body['data_fim'].replace('Z', '+00:00'))
        
        promocao = Promocao(**req_body)
        promocao_criada = service.criar_promocao(promocao)
        
        return func.HttpResponse(
            promocao_criada.model_dump_json(),
            status_code=201,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"erro": f"Erro ao criar promoção: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )


def handle_put(service: PromocaoService, promocao_id: Optional[str], req: func.HttpRequest) -> func.HttpResponse:
    """Trata requisições PUT (atualizar promoção)"""
    if not promocao_id:
        return func.HttpResponse(
            json.dumps({"erro": "ID da promoção é obrigatório para atualização"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"erro": "JSON inválido"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        # Converte strings de data para datetime se necessário
        if isinstance(req_body.get('data_inicio'), str):
            req_body['data_inicio'] = datetime.fromisoformat(req_body['data_inicio'].replace('Z', '+00:00'))
        if isinstance(req_body.get('data_fim'), str):
            req_body['data_fim'] = datetime.fromisoformat(req_body['data_fim'].replace('Z', '+00:00'))
        
        # Atualiza o timestamp de atualização
        req_body['atualizado_em'] = datetime.now(timezone.utc)
        
        promocao = Promocao(**req_body)
        promocao_atualizada = service.atualizar_promocao(promocao_id, promocao)
        
        return func.HttpResponse(
            promocao_atualizada.model_dump_json(),
            status_code=200,
            mimetype="application/json"
        )
    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"erro": str(e)}),
            status_code=404,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"erro": f"Erro ao atualizar promoção: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )


def handle_delete(service: PromocaoService, promocao_id: Optional[str]) -> func.HttpResponse:
    """Trata requisições DELETE"""
    if not promocao_id:
        return func.HttpResponse(
            json.dumps({"erro": "ID da promoção é obrigatório para exclusão"}),
            status_code=400,
            mimetype="application/json"
        )
    
    deleted = service.deletar_promocao(promocao_id)
    if deleted:
        return func.HttpResponse(
            json.dumps({"mensagem": "Promoção deletada com sucesso"}),
            status_code=200,
            mimetype="application/json"
        )
    else:
        return func.HttpResponse(
            json.dumps({"erro": "Promoção não encontrada"}),
            status_code=404,
            mimetype="application/json"
        )
