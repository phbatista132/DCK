import pandas as pd
import os

class Produto:
    def __init__(self):
        self.produtos = []

    def dados(self, modelo, categoria, valor, codigo, estoque):
        self.produtos.append({
            'modelo': modelo,
            'categoria': categoria,
            'valor': valor,
            'codigo': codigo,
            'estoque': estoque
        })

    @staticmethod
    def listar_produtos():
        df = pd.read_csv("estoque.csv", encoding='latin1', sep=',')
        print(df)


    @staticmethod
    def estoque():
        return pd.read_csv("estoque.csv")


class SistemaPrincipal:
    def __init__(self, estoque="C:/Users/phbat/OneDrive/Desktop/DCK/src/utils/estoque.csv"):
        self.gerenciaprod = Produto()
        self.docs = estoque

    def cadastrar_produto(self):
        modelo = input("MODELO: ").strip().lower()
        tipo = input("TIPO: ").strip().lower()
        valor = float(input("VALOR: ").replace(',', '.'))
        estoque =  int(input("Quantidade: "))


        if os.path.isfile(self.docs) and os.path.getsize(self.docs) > 0:
            df_existente = pd.read_csv(self.docs)
            if 'codigo' in df_existente.columns and not df_existente['codigo'].empty:
                codigo = int(df_existente['codigo'].max()) + 1
            else:
                codigo = 1
        else:
            codigo = 1

        self.gerenciaprod.dados(modelo, tipo, valor, codigo, estoque)
        df_novo = pd.DataFrame(self.gerenciaprod.produtos)
        arquivo_vazio = not os.path.isfile(self.docs) or os.path.getsize(self.docs) == 0

        # ✅ Salva com cabeçalho apenas se o arquivo estiver vazio ou não existir
        df_novo.to_csv(self.docs, mode='a', header=arquivo_vazio, index=False)

        self.gerenciaprod.produtos.clear()
        return "✅ Produto cadastrado com sucesso!"


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


    def reposicao(self, id, qtd):
        df = pd.read_csv(self.docs, encoding = 'utf-8', sep=',')
        if id in df['codigo'].values:
            if qtd <= 0:
                print("Quantidade menor ou igual a zero, sem possibilidade de repor")
            else:
                df.loc[df['codigo'] == id, 'quantidade'] += qtd
                df.to_csv(self.docs, index=False, encoding='utf-8')
                # Salva o dados atualizados no csv
                modelo = df.loc[df['codigo'] == id, 'modelo'].values[0]
                print(f"Estoque do item {modelo} reposto")
        else:
            print("id não localizado")
