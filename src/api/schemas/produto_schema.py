"""
Esquemas pydantic para produto
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal, ROUND_DOWN
from typing import Optional


@field_validator('vlr_compra', 'valor')
def validar_casas_decimais(cls, v: Decimal) -> Decimal:
    if v.as_tuple().exponent < -2:
        raise ValueError("O Valor deve ter no maximo duas casas decimais")
    return v.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

class ProdutoCreated(BaseModel):
    nome: str = Field(..., min_length=3, description="Nome do produto")
    modelo: str = Field(..., min_length=3, description="Modelo do produto")
    categoria: str = Field(..., min_length=3, description="Categoria do produto")
    quantidade_estoque: int = Field(...,gt=0, description="Quantidade")
    valor: Decimal = Field(...,gt=0, description="Valor do produto")
    vlr_compra: Decimal = Field(...,gt=0, description="Valor da compra")

    @field_validator('vlr_compra', 'valor')
    def validar_casas_decimais(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -2:
            raise ValueError("O Valor deve ter no maximo duas casas decimais")
        return v.quantize(Decimal('0.01'), rounding=ROUND_DOWN)


    @model_validator(mode="after")
    def validar_vlr_compra_menor_venda(self):
        if self.vlr_compra > self.valor:
            raise ValueError("O valor de venda não pode ser menor que o valor de compra")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Notebook Dell",
                "modelo": "Inspiron 15",
                "categoria": "Eletrônicos",
                "quantidade_estoque": 100,
                "valor": 3500.00,
                "vlr_compra": 2800.00,
            }
        }

class ProdutoUpdate(BaseModel):
    """Schema para edição de produtos"""
    nome: Optional[str] = Field(None, min_length=3, description="Nome do produto")
    modelo: Optional[str] = Field(None, min_length=3, description="Modelo do produto")
    valor: Optional[Decimal] = Field(None, gt=0, le=1000000, description="Valor do produto")
    vlr_compra: Optional[Decimal] = Field(None, gt=0, description="Valor de compra")

    @field_validator('vlr_compra', 'valor')
    def validar_casas_decimais(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -2:
            raise ValueError("O Valor deve ter no maximo duas casas decimais")
        return v.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    @model_validator(mode="after")
    def validar_vlr_compra_menor_venda(self):
        if self.vlr_compra > self.valor:
            raise ValueError("O valor de venda não pode ser menor que o valor de compra")
        return self

    @field_validator('valor')
    def validar_valor_razoavel(cls, v):
        if v and v > 100000:
            pass
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Notebook Dell",
                "modelo": "Inspiron 15",
                "valor": 3800.00,
                "vlr_compra": 2900.00,
            }
        }