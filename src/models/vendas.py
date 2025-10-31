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
            raise ValueError("Preço unitario não pode ser negativo")

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
    data_finalizacao: Optional[datetime] = None

    def __post_init__(self):
        if not self.itens:
            raise ValueError("Venda deve ter pelo menos um item")

        self.subtotal = self._calcular_subtota()
        self.total = self.subtotal

        if self.data_finalizacao is None:
            self.data_finalizacao = datetime.now()

    def _calcular_subtota(self) -> float:
        return  sum(item.subtotal for item in self.itens)

    def aplicar_desconto(self, percentual: float) -> float:
        if not (0 <= percentual <= 100):
            raise ValueError("Desconto deve estar entre 0 e 100")

        valor_desconto = self.total * (percentual / 100)
        formatado = Decimal(str(valor_desconto)).quantize(Decimal("0.00"), rounding=ROUND_DOWN)
        self.desconto = float(formatado)

        self.total = self.subtotal - self.desconto

        return self.desconto


    def tem_cliente(self):
        return  self.cliente_id is not None

    def to_dict(self) -> dict:

        return {
            "id_venda": self.id_venda,
            "data": self.data_hora.isoformat(),
            "itens": self.itens,
            "subtotal": self.subtotal,
            "total": self.total,
            "desconto": self.desconto,
            "forma_pagamento":self.forma_pagamento,
            "status": self.status,
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