from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Cliente:
    """Representa um cliente do sistema"""
    nome: str
    cpf: str
    dt_nascimento: date
    telefone: str
    endereco: str
    ativo: bool = True
    data_cadastro: Optional[date] = None

    def __post_init__(self):
        """Validações automaticas"""

        if self.data_cadastro is None:
            self.data_cadastro = date.today()

        if not self.nome or len(self.nome.strip()) < 3:
            raise ValueError("Nome deve conter 3 caracteres no minimo")

        self.cpf = ''.join(filter(str.isdigit, self.cpf))

        if not self.cpf.isdigit() or len(self.cpf) != 11:
            raise ValueError("CPF deve ter 11 dígitos")

    def calcular_idade(self) -> int:
        hoje = date.today()
        return hoje.year - self.dt_nascimento.year - (
                    (hoje.month, hoje.day) < (self.dt_nascimento.month, self.dt_nascimento.day)
        )
    def maior_idade(self) -> bool:
        return self.calcular_idade() >= 18

    def desativar(self) -> None:
        """Desativa cliente"""
        self.ativo = False

    def esta_ativo(self) -> bool:
        """Verifica se o cliente esta ativo"""
        return self.ativo

    def to_dict(self) -> dict:
        """Converte para dicionario"""
        return {
            'nome': self.nome,
            'cpf': self.cpf,
            'dt_nascimento': self.dt_nascimento.strftime("%d/%m/%Y") if isinstance(self.dt_nascimento, date) else self.dt_nascimento,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'Cliente':
        """Cria cliente a partir de um dicionario"""
        return Cliente(
            nome=data['nome'],
            cpf=data['cpf'],
            dt_nascimento= datetime.strptime(data['dt_nascimento'], "%d/%m/%Y").date() if isinstance(data['dt_nascimento'], str) else data['dt_nascimento'],
            telefone=data['telefone'],
            endereco=data['endereco'],
            ativo=data.get('ativo', True),
            data_cadastro=date.fromisoformat(data['data_cadastro']) if data.get('data_cadastro') else None,
        )

    def __str__(self) -> str:
        return f"Cliente: {self.nome} | CPF: {self.cpf} | Telefone: {self.telefone}"