from typing import TypedDict, List
from datetime import datetime



class ItemVenda(TypedDict):
    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: float
    subtotal: float


class Vendas:
    def __init__(self):
        self.vendas = {}
        self.itens_atuais = []


    def dados_vendas(self, id_venda: int, data: datetime, cliente_id: int | None, itens: List[ItemVenda], total: float,
                     desconto: float, forma_pagamento:str):
        """Prepara venda para salvar em CSV"""

        self.vendas = {
            "id_venda": id_venda,
            "data": data.isoformat(),
            "cliente_id": cliente_id,
            "itens": itens,
            "total": total,
            "desconto": desconto,
            "forma_pagamento": forma_pagamento,
            "status": "finalizada",
            "data_finalizacao": datetime.now().isoformat()
        }

        self.itens_atuais = []
        for idx, item in enumerate(itens, start=1):
            self.itens_atuais.append({
                'id_item': f"{id_venda}_{idx}",
                'id_venda': id_venda,
                'produto_id': item['produto_id'],
                'nome_produto': item.get('nome_produto', ""),
                'quantidade': item['quantidade'],
                'preco_unitario': item['preco_unitario'],
                'subtotal': item['subtotal'],
            })

