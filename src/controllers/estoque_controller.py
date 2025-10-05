import pandas as pd
from src.controllers import Produto


class EstoqueController:
    def __init__(self, estoque='C:/Users/phbat/OneDrive/Desktop/DCK/data/estoque.csv'):
        self.produto_estoque = Produto()
        self.estoque_data = estoque

    def reposicao(self, id_item, qtd):
        try:
            df = pd.read_csv(self.estoque_data, encoding='utf-8', sep=',')
            if id_item in df['codigo'].values:
                if qtd <= 0:
                    return "Quantidade menor ou igual a zero, sem possibilidade de repor"
                else:
                    df.loc[df['codigo'] == id_item, 'quantidade'] += qtd
                    df.to_csv(self.estoque_data, index=False, encoding='utf-8')
                    modelo = df.loc[df['codigo'] == id_item, 'modelo'].values[0]
                    return f"Estoque do item {modelo} reposto"
            else:
                return "id não localizado"
        except Exception as e:
            return f'Erro ao repor produto: {e}'

    def disponibilidade(self, id_produto, quantidade):
        try:
            df = pd.read_csv(self.estoque_data, encoding='utf-8', sep=',')
            if id_produto in df['codigo'].values:
                estoque_atual = df.loc[df['codigo'] == id_produto, 'quantidade_estoque'].values[0]

                if estoque_atual >= quantidade:
                    return True, f'Disponível: {estoque_atual} unidades'
                else:
                    return False, f'Insuficiente: {estoque_atual} disponível (solicitado: {quantidade})'
            else:
                return False, 'Produto não localizado em estoque'

        except Exception as e:
            return False, f'Erro: {e}'


