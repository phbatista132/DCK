from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class EstoqueReposicaoRequest(BaseModel):
    """Schema para requisição de reposição de estoque"""
    quantidade: int = Field(
        ...,
        gt=0,
        description="Quantidade a ser adicionada ao estoque",
        examples=[50, 100]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quantidade": 100
            }
        }


class EstoqueReposicaoResponse(BaseModel):
    """Schema para resposta de reposição"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Item reposto com sucesso",
                "data": {
                    "id_produto": 1,
                    "quantidade_adicionada": 100
                }
            }
        }


class ReservasResponse(BaseModel):
    """Schema para resposta de reservas"""
    success: bool
    total_reservas: int
    reservas: Dict[int, Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_reservas": 2,
                "reservas": {
                    "1": {
                        "quantidade": 5,
                        "expira_em": "2025-11-08T15:30:00",
                        "tempo_restante_minutos": 28
                    }
                }
            }
        }


class DisponibilidadeResponse(BaseModel):
    """Schema para resposta de disponibilidade"""
    success: bool
    id_produto: int
    disponivel: bool
    estoque_disponivel: int
    quantidade_solicitada: int
    produto_ativo: bool
    message: str