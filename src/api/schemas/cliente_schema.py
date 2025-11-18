"""
Schemas Pydantic para validação de dados
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ClienteCreate(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=14, description="CPF")
    nome: str = Field(..., min_length=1, max_length=100, description="Nome")
    dt_nascimento: str = Field(..., pattern=r"^\d{2}/\d{2}/\d{4}$", description="Data de nascimento")
    endereco: str = Field(..., min_length=5, max_length=500, description="Endereço completo")
    telefone: str = Field(..., min_length=10, max_length=15, description="Telefone com DDD")

    @field_validator('cpf')
    def cpf_validator(cls, v):
        """Remove formatação do CPF"""
        return ''.join(filter(str.isdigit, v))

    class Config:
        json_schema_extra = {
            "example": {
                "cpf": "123.456.789.00",
                "nome": "João da Silva",
                "dt_nascimento": "01/01/1990",
                "endereco": "Rua do Brasil",
                "telefone": "(11) 98161-1681",
            }
        }


class ClienteUpdate(BaseModel):
    """Schema para atualização de cliente (campos opcionais)"""

    telefone: Optional[str] = Field(None, min_length=10, max_length=15)
    endereco: Optional[str] = Field(None, min_length=5, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "telefone": "(11) 91111-5555",
                "endereco": "Rua São Paulo, Brasil",
            }
        }

class ClienteResponse(BaseModel):
    """Schema para resposta de cliente"""
    id_cliente: int
    nome: str
    cpf: str
    dt_nascimento: datetime
    telefone: str
    endereco: str
    ativo: bool
    data_cadastro: Optional[datetime] = None

    class Config:
        from_attributes = True