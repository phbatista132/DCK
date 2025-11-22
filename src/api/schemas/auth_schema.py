from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UsuarioRegistro(BaseModel):
    """Schema para registro de novo usuario"""
    username : str = Field(..., min_length=3, max_length=20, description="Nome de usuario")
    email: EmailStr = Field(...,description="Email")
    senha: str = Field(..., min_length=6, max_length=20, description="Senha")
    nome_completo: str = Field(..., min_length=3, max_length=200, description="Nome completo")
    tipo_usuario: str = Field(...,pattern="^(admin|gerente|vendedor)$", description="Tipo de usuario")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "joao.silva",
                "email": "joao@email.com",
                "senha": "SenhaSegura123!",
                "nome_completo": "João Silva",
                "tipo_usuario": "vendedor"
            }
        }

class UsuarioLogin(BaseModel):
    """Schema para login"""
    username: str = Field(..., min_length=3, description="Username")
    senha: str = Field(..., min_length=8, description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "joao.silva",
                "password": "SenhaSegura123!"
            }
        }
class TokenResponse(BaseModel):
    """Schema de resposta com tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RefreshTokenRequest(BaseModel):
    """Schema para renovar token"""
    refresh_token: str = Field(..., description="Refresh token valido")

class AlterarSenhaRequest(BaseModel):
    """Schema para alterar senha"""
    senha_atual: str = Field(..., min_length=8, description="Senha atual")
    nova_senha: str = Field(..., min_length=8, description="Nova senha")

    class config:
        json_schema_extra = {
            "example": {
                "senha_atual": "SenhaAntiga123!",
                "nova_senha": "NovaSenha456!"
            }
        }

class UsuarioResponse(BaseModel):
    """Schema de resposta de usuário (sem dados sensíveis)"""
    id_usuario: int
    username: str
    email: str
    nome_completo: str
    tipo_usuario: str
    ativo: bool
    data_cadastro: str
    ultimo_acesso: Optional[str] = None