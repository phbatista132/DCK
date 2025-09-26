import pandas as pd
from src.utils import SistemaAdm, Produto
from logging import log


class Vendas:
    def __init__(self):
        self.cliente = SistemaAdm
        self.obter_estoque = Produto.estoque

    def venda(self, codigo, quantidade):
        df = self.obter_estoque()
        if codigo not in df['codigo'].values:
            print('Codigo não localizado')
            return

        if quantidade <= 0:
            print("Quantidade menor que 0, impossivel seguir com a compra")
            return

        estoque_atual = df.loc[df['codigo'] == codigo, 'quantidade'].values[0]
        if quantidade > estoque_atual:
            print(f'Estoque insuficiente! Estoque: {estoque_atual}')
            return


        df.loc[df['codigo'] == codigo, 'quantidade'] -= quantidade

        #Verificar chamada do init self.obter_estoque, retorna erro de method ou function
        df.to_csv(self.obter_estoque(), index=False, encoding='utf-8')

        print(f"✅ Compra do item finalizada com sucesso.")

