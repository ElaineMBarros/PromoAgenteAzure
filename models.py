"""
Modelo de dados para Promoções
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from uuid import uuid4


class Promocao(BaseModel):
    """Modelo de dados para uma promoção"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Black Friday - Produto X",
                "descricao": "Desconto especial de Black Friday no Produto X",
                "valor_original": 100.00,
                "valor_promocional": 70.00,
                "data_inicio": "2024-11-01T00:00:00",
                "data_fim": "2024-11-30T23:59:59",
                "ativa": True,
                "categoria": "Eletrônicos"
            }
        }
    )
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    nome: str = Field(..., min_length=1, max_length=200, description="Nome da promoção")
    descricao: str = Field(..., min_length=1, description="Descrição detalhada da promoção")
    valor_original: float = Field(..., gt=0, description="Valor original do produto/serviço")
    valor_promocional: float = Field(..., gt=0, description="Valor promocional")
    percentual_desconto: Optional[float] = Field(None, description="Percentual de desconto")
    data_inicio: datetime = Field(..., description="Data de início da promoção")
    data_fim: datetime = Field(..., description="Data de término da promoção")
    ativa: bool = Field(default=True, description="Status da promoção")
    categoria: Optional[str] = Field(None, max_length=100, description="Categoria da promoção")
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode='after')
    def validar_e_calcular(self):
        """Valida valores e calcula percentual de desconto"""
        # Valida se o valor promocional é menor que o valor original
        if self.valor_promocional >= self.valor_original:
            raise ValueError('Valor promocional deve ser menor que o valor original')
        
        # Valida se a data de término é posterior à data de início
        if self.data_fim <= self.data_inicio:
            raise ValueError('Data de término deve ser posterior à data de início')
        
        # Calcula o percentual de desconto automaticamente se não fornecido
        if self.percentual_desconto is None and self.valor_original > 0:
            self.percentual_desconto = ((self.valor_original - self.valor_promocional) / self.valor_original) * 100
        
        return self
