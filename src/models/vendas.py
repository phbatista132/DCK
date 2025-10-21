from typing import TypedDict, List
from datetime import datetime


class ItemVenda(TypedDict):
    produto_id: int
    quantidade: int
    preco_unitario: float
    subtotal: float


class Vendas:
    def __init__(self):
        self.vendas = []

    def dados_vendas(self, id_venda: int, data: datetime, cliente_id: int | None, itens: List[ItemVenda], total: float,
                     desconto: float, forma_pagamento:str):
        self.vendas.append({
            "id_venda": id_venda,
            "data": data,
            "cliente_id": cliente_id,
            "itens": itens,
            "total": total,
            "desconto": desconto,
            "forma_pagamento": forma_pagamento,
            "status": "finalizada"
        })
