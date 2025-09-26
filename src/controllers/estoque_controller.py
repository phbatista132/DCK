import pandas as pd
from src.controllers import Produto

class SistemaEstoque:
    def __init__(self, estoque="C:/Users/phbat/OneDrive/Desktop/DCK/src/utils/estoque.csv"):
        self.gerenciaprod = Produto()
        self.docs = estoque

    def deletar_produto(self):
        df = pd.read_csv(self.docs, encoding='latin1', sep=",")
        idbusca = int(input("ID: "))
        if idbusca in df['codigo'].values:
            df = df[df['codigo'] != idbusca]
            df.to_csv(self.docs, index=False)
            return 'Item deletado da base de dados!'
        else:
            return 'Codigo não localizada na base de dados'



    def filtrar_produto(self):
        df = pd.read_csv(self.docs, encoding='latin1', sep=',')
        categoria = int(input("Digite o codigo do produto: ").strip().lower())
        filtro = df[df['codigo'] == categoria]
        return filtro


    def reposicao(self, id_item, qtd):
        df = pd.read_csv(self.docs, encoding = 'utf-8', sep=',')
        if id_item in df['codigo'].values:
            if qtd <= 0:
                print("Quantidade menor ou igual a zero, sem possibilidade de repor")
            else:
                df.loc[df['codigo'] == id_item, 'quantidade'] += qtd
                # Salva o dados atualizados no csv
                df.to_csv(self.docs, index=False, encoding='utf-8')
                modelo = df.loc[df['codigo'] == id_item, 'modelo'].values[0]
                print(f"Estoque do item {modelo} reposto")
        else:
            print("id não localizado")