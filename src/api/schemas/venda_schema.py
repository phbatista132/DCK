from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class ItemCarrinhoRequest(BaseModel):
    """Schema para adicionar item ao carrinho"""
    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: int = Field(..., gt=0, le=1000, description="Quantidade desejada")

    class Config:
        json_schema_extra = {
            "example": {
                "produto_id": 1,
                "quantidade": 2
            }
        }


class AlterarQuantidadeRequest(BaseModel):
    """Schema para alterar quantidade no carrinho"""
    nova_quantidade: int = Field(..., gt=0, le=1000, description="Nova quantidade")

    class Config:
        json_schema_extra = {
            "example": {
                "nova_quantidade": 5
            }
        }


class ItemCarrinhoResponse(BaseModel):
    """Schema de resposta de item do carrinho"""
    produto_id: int
    nome: str
    quantidade: int
    preco_unitario: float
    subtotal: float


class CarrinhoResponse(BaseModel):
    """Schema de resposta do carrinho"""
    success: bool
    total_itens: int
    subtotal: float
    itens: List[ItemCarrinhoResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_itens": 2,
                "subtotal": 7000.00,
                "itens": [
                    {
                        "produto_id": 1,
                        "nome": "Notebook Dell",
                        "quantidade": 2,
                        "preco_unitario": 3500.00,
                        "subtotal": 7000.00
                    }
                ]
            }
        }


class FinalizarVendaRequest(BaseModel):
    """Schema para finalizar venda"""
    cpf_cliente: Optional[str] = Field(
        None,
        min_length=11,
        max_length=14,
        description="CPF do cliente (opcional)"
    )
    forma_pagamento: str = Field(
        "Debito",
        description="Forma de pagamento",
        pattern="^(Debito|Credito|Dinheiro|PIX)$"
    )
    percentual_desconto: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Percentual de desconto (0-100)"
    )

    @field_validator('cpf_cliente')
    def limpar_cpf(cls, v):
        """Remove formatação do CPF"""
        if v:
            return ''.join(filter(str.isdigit, v))
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "cpf_cliente": "12345678900",
                "forma_pagamento": "Credito",
                "percentual_desconto": 10.0
            }
        }


class FinalizarVendaResponse(BaseModel):
    """Schema de resposta de venda finalizada"""
    success: bool
    message: str
    id_venda: Optional[int] = None
    total: Optional[float] = None
    desconto_aplicado: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Venda finalizada com sucesso",
                "id_venda": 42,
                "total": 6300.00,
                "desconto_aplicado": 700.00
            }
        }
