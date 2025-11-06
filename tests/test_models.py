"""
Testes unitários para o modelo Promocao
"""
import pytest
from datetime import datetime, timedelta
from models import Promocao


def test_criar_promocao_valida():
    """Testa criação de promoção com dados válidos"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    promocao = Promocao(
        nome="Teste Promoção",
        descricao="Descrição de teste",
        valor_original=100.0,
        valor_promocional=70.0,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    assert promocao.nome == "Teste Promoção"
    assert promocao.valor_original == 100.0
    assert promocao.valor_promocional == 70.0
    assert promocao.ativa is True
    assert promocao.id is not None


def test_calcular_percentual_desconto():
    """Testa cálculo automático do percentual de desconto"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    promocao = Promocao(
        nome="Teste",
        descricao="Teste",
        valor_original=100.0,
        valor_promocional=70.0,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    assert promocao.percentual_desconto == 30.0


def test_valor_promocional_maior_que_original():
    """Testa validação quando valor promocional é maior que o original"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    with pytest.raises(ValueError, match="Valor promocional deve ser menor que o valor original"):
        Promocao(
            nome="Teste",
            descricao="Teste",
            valor_original=70.0,
            valor_promocional=100.0,
            data_inicio=data_inicio,
            data_fim=data_fim
        )


def test_data_fim_antes_da_data_inicio():
    """Testa validação quando data fim é anterior à data início"""
    data_inicio = datetime.now()
    data_fim = data_inicio - timedelta(days=1)
    
    with pytest.raises(ValueError, match="Data de término deve ser posterior à data de início"):
        Promocao(
            nome="Teste",
            descricao="Teste",
            valor_original=100.0,
            valor_promocional=70.0,
            data_inicio=data_inicio,
            data_fim=data_fim
        )


def test_valor_original_zero():
    """Testa validação quando valor original é zero"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    with pytest.raises(ValueError):
        Promocao(
            nome="Teste",
            descricao="Teste",
            valor_original=0.0,
            valor_promocional=70.0,
            data_inicio=data_inicio,
            data_fim=data_fim
        )


def test_nome_vazio():
    """Testa validação quando nome está vazio"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    with pytest.raises(ValueError):
        Promocao(
            nome="",
            descricao="Teste",
            valor_original=100.0,
            valor_promocional=70.0,
            data_inicio=data_inicio,
            data_fim=data_fim
        )


def test_promocao_com_categoria():
    """Testa criação de promoção com categoria"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    promocao = Promocao(
        nome="Teste",
        descricao="Teste",
        valor_original=100.0,
        valor_promocional=70.0,
        data_inicio=data_inicio,
        data_fim=data_fim,
        categoria="Eletrônicos"
    )
    
    assert promocao.categoria == "Eletrônicos"


def test_promocao_json_serialization():
    """Testa serialização para JSON"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    promocao = Promocao(
        nome="Teste",
        descricao="Teste",
        valor_original=100.0,
        valor_promocional=70.0,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    json_str = promocao.model_dump_json()
    assert json_str is not None
    assert "Teste" in json_str
    assert "100.0" in json_str


def test_timestamps_automaticos():
    """Testa criação automática de timestamps"""
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=30)
    
    promocao = Promocao(
        nome="Teste",
        descricao="Teste",
        valor_original=100.0,
        valor_promocional=70.0,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    assert promocao.criado_em is not None
    assert promocao.atualizado_em is not None
    assert isinstance(promocao.criado_em, datetime)
    assert isinstance(promocao.atualizado_em, datetime)
