from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

@dataclass
class Usuario:
    """
    Model de Usuario do sistema

    Niveis de permissão
    - admin: Acesso total (gerenciar usuários, estoque, vendas)
    - gerente: Gerenciar Vendas e estoque
    - vendedor: Apenas registrar vendas
    """
    id_usuario: int
    username: str
    email: str
    senha_hash:  str
    nome_completo: str
    tipo_usuario: str
    ativo: bool = True
    data_cadastro: date =field(default_factory=date.today)
    ultimo_acesso: Optional[int] = None

    def to_dict(self) -> dict:
        """Converte para dicionario"""
        return {
            "id_usuario": self.id_usuario,
            "username": self.username,
            "email": self.email,
            "senha_hash": self.senha_hash,
            "nome_completo": self.nome_completo,
            "tipo_usuario": self.tipo_usuario,
            "ativo": self.ativo,
            "data_cadastro": self.data_cadastro,
            "ultimo_acesso": self.ultimo_acesso,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Usuario':
        """Criar instância a partir de um dicionario"""
        return cls(
            id_usuario=data["id_usuario"],
            username=data["username"],
            email=data["email"],
            senha_hash=data["senha_hash"],
            nome_completo=data["nome_completo"],
            tipo_usuario=data["tipo_usuario"],
            ativo=data["ativo"],
            data_cadastro=date.fromisoformat(data["data_cadastro"]),
            ultimo_acesso=datetime.fromisoformat(data["ultimo_acesso"]) if data.get("ultimo_acesso") else None,
        )

    def to_dict_safe(self) -> dict:
        """Retorna dados seguros"""
        safe_data = self.to_dict()
        safe_data.pop('senha_hash', None)
        return safe_data