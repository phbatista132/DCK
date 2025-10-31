from dataclasses import dataclass
from datetime import date


@dataclass
class Produto:
    nome: str
    modelo: str
    categoria: str
    valor: float
    codigo: int
    quantidade_estoque: int
    dt_cadastro: date
    vlr_compra: float
    margem_lucro: float
    ativo: bool = True
    def __post_init__(self):
        """Validações automaticas"""

        if self.valor < 0:
            raise ValueError("Valor deve ser positivo")
        if self.vlr_compra < 0 and self.vlr_compra < self.valor:
            raise ValueError("Valor de compra deve ser positivo e menor que valor de venda")
        if self.quantidade_estoque < 0:
            raise ValueError("Quantidade estoque deve ser positivo")

        self.margem_lucro = self.calcular_margem()

    def calcular_margem(self) -> float:
        """Calcula o valor da margem de lucro"""
        if self.vlr_compra == 0:
            return 0.0
        return round(((self.vlr_compra * self.margem_lucro)/ self.vlr_compra) * 100, 2)

    def desativar(self) -> None:
        """Desativar produto"""
        self.ativo = False

    def esta_ativo(self) -> bool:
        """Verifica se produto esta ativo"""
        return self.ativo

    def to_dict(self) -> dict:
        """Convertendo para dicionario"""
        return {
            'nome': self.nome,
            'modelo': self.modelo,
            'categoria': self.categoria,
            'valor': self.valor,
            'codigo': self.codigo,
            'quantidade_estoque': self.quantidade_estoque,
            'data_cadastro': self.dt_cadastro.isoformat(),
            'vlr_compra': self.vlr_compra,
            'margem_lucro': self.margem_lucro,
            'ativo': self.ativo
            }

    def __str__(self) -> str:
        """Formatação para exibição"""
        return (
            f"Produto: {self.nome} | Modelo: {self.modelo} | "
            f"Categoria: {self.categoria} | Valor: R$ {self.valor:.2f} | "
            f"Quantidade: {self.quantidade_estoque}"
        )
