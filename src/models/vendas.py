from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN


@dataclass
class ItemVenda:
    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: float
    subtotal: float

    def __post_init__(self):
        if self.quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva")
        if self.preco_unitario < 0:
            raise ValueError("Preço unitário não pode ser negativo")

        self.subtotal = float(
            Decimal(str(self.quantidade * self.preco_unitario)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        )


@dataclass
class Venda:

    id_venda: int
    data_hora: datetime
    itens: List[ItemVenda]
    subtotal: float
    total: float
    desconto: float
    forma_pagamento: str
    status: str = "finalizada"
    cliente_id: Optional[int] = None
    vendedor_id: Optional[int] = None
    vendedor_nome: Optional[str] = None
    data_finalizacao: Optional[datetime] = None

    def __post_init__(self):
        if not self.itens:
            raise ValueError("Venda deve ter pelo menos um item")

        self.subtotal = float(Decimal(str(self._calcular_subtotal())).quantize(Decimal('0.01'), rounding=ROUND_DOWN))
        self.total = self.subtotal

        if self.data_finalizacao is None:
            self.data_finalizacao = datetime.now()

    def _calcular_subtotal(self) -> float:
        return  sum(item.subtotal for item in self.itens)

    def aplicar_desconto(self, percentual: float) -> float:
        if not (0 <= percentual <= 100):
            raise ValueError("Desconto deve estar entre 0 e 100")

        valor_desconto = self.subtotal * (percentual / 100)
        self.desconto = float(Decimal(str(valor_desconto)).quantize(Decimal("0.00"), rounding=ROUND_DOWN))

        self.total = self.subtotal - self.desconto

        return self.desconto


    def tem_cliente(self):
        return  self.cliente_id is not None

    def to_dict(self) -> dict:

        return {
            "id_venda": self.id_venda,
            "database": self.data_hora.isoformat(),
            "cliente_id": self.cliente_id,
            "itens": self.itens,
            "subtotal": self.subtotal,
            "total": self.total,
            "desconto": self.desconto,
            "forma_pagamento":self.forma_pagamento,
            "status": self.status,
            "vendedor_id": self.vendedor_id,
            "vendedor_nome": self.vendedor_nome,
            "data_finalizacao": self.data_finalizacao.isoformat(),
        }

    def itens_to_list(self)-> List[dict]:
        return [
            {
                'id_item': f"{self.id_venda}_{idx}",
                'id_venda': self.id_venda,
                'produto_id': item.produto_id,
                'nome_produto': item.nome_produto,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'subtotal': item.subtotal
            }
            for idx, item in enumerate(self.itens, start=1)
        ]