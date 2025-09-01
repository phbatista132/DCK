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
    def __init__(self):
        self.gerenciaprod = Produto()

    def cadastrar_produto(self):
        modelo = input("MODELO: ").strip().lower()
        tipo = input("TIPO: ").strip().lower()
        valor = float(input("VALOR: ").replace(',', '.'))
        estoque =  int(input("Quantidade: "))
        arquivo = 'estoque.csv'

        if os.path.isfile(arquivo) and os.path.getsize(arquivo) > 0:
            df_existente = pd.read_csv(arquivo)
            if 'codigo' in df_existente.columns and not df_existente['codigo'].empty:
                codigo = int(df_existente['codigo'].max()) + 1
            else:
                codigo = 1
        else:
            codigo = 1

        self.gerenciaprod.dados(modelo, tipo, valor, codigo, estoque)
        df_novo = pd.DataFrame(self.gerenciaprod.produtos)
        arquivo_vazio = not os.path.isfile(arquivo) or os.path.getsize(arquivo) == 0

        # ✅ Salva com cabeçalho apenas se o arquivo estiver vazio ou não existir
        df_novo.to_csv(arquivo, mode='a', header=arquivo_vazio, index=False)

        self.gerenciaprod.produtos.clear()
        return "✅ Produto cadastrado com sucesso!"

    @staticmethod
    def deletar_produto():
        df = pd.read_csv("estoque.csv", encoding='latin1', sep=",")
        idbusca = int(input("ID: "))
        if idbusca in df['codigo'].values:
            df = df[df['codigo'] != idbusca]
            df.to_csv("estoque.csv", index=False)
            return 'Item deletado da base de dados!'
        else:
            return 'Codigo não localizada na base de dados'


    @staticmethod
    def filtrar_produto():
        df = pd.read_csv("estoque.csv", encoding='latin1', sep=',')
        categoria = int(input("Digite o codigo do produto: ").strip().lower())
        filtro = df[df['codigo'] == categoria]
        return filtro


    #def reposicao(self):









def main():
    produto = Produto()
    sis_principal = SistemaPrincipal()
    while True:
        try:
            opc = int(input("Selecione uma Opção: "))

            if opc == 1:
                print(sis_principal.cadastrar_produto())
            elif opc == 2:
                produto.listar_produtos()
            elif opc == 3:
                print(sis_principal.deletar_produto())
            elif opc == 4:
                print(sis_principal.filtrar_produto())
            elif opc == 0:
                print("Saindo do programa!")
                break
            else:
                print("❌ Opção inválida.")
        except Exception as e:
            print(f"⚠️ Erro: {e}")


if __name__ == "__main__":
    main()









