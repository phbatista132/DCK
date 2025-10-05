from src.controllers import Produto
import os
import pandas as pd
from datetime import date


def gerar_arquivo(arquivo='C:/Users/phbat/OneDrive/Desktop/DCK/data/estoque.csv'):
    if not os.path.exists(arquivo):
        with open(arquivo, mode='w', newline="", encoding='utf-8') as f:
            pass


def data_cadastro():
    return date.today()


def duplicado(arquivo, nome, modelo, categoria):
    df = pd.read_csv(arquivo, encoding='utf-8', sep=',')
    duplicada = df[(df['nome'] == nome) &
                   (df['modelo'] == modelo) &
                   (df['categoria'] == categoria)]
    return duplicada.empty


class ProdutoController:
    def __init__(self, produtos_data='C:/Users/phbat/OneDrive/Desktop/DCK/data/estoque.csv'):
        self.produto_model = Produto()
        self.produtos_data = produtos_data

    def gera_codigo(self) -> int:
        codigo = 1
        if os.path.isfile(self.produtos_data) and os.path.getsize(self.produtos_data) > 0:
            try:
                df_existente = pd.read_csv(self.produtos_data, )
                if 'codigo' in df_existente.columns and not df_existente['codigo'].empty and not df_existente[
                    'codigo'].isna().all():
                    codigo = int(df_existente['codigo'].max()) + 1
                else:
                    codigo = 1

            except Exception as e:
                print(f'Erro ao ler csv: {e}')

        return codigo

    def cadastrar_produto(self, nome, modelo, categoria, valor: float, quantidade_estoque: int, vlr_compra: float):
        try:
            gerar_arquivo()
            if self.produto_model.validar_dados(valor, vlr_compra, quantidade_estoque):
                if duplicado(self.produtos_data, nome, modelo, categoria):
                    self.produto_model.dados(nome, modelo, categoria, valor, self.gera_codigo(), quantidade_estoque,
                                             data_cadastro(),
                                             vlr_compra, self.produto_model.margem_lucro(valor, vlr_compra))
                    salvar_produto = pd.DataFrame(self.produto_model.produtos)
                    arquivo_vazio = not os.path.isfile(self.produtos_data) or os.path.getsize(self.produtos_data) == 0
                    salvar_produto.to_csv(self.produtos_data, mode='a', header=arquivo_vazio, index=False)
                    self.produto_model.produtos.clear()
                    return "✅ Produto cadastrado com sucesso!"
                else:
                    return "Produto duplicado, cadastro não realizado"

        except Exception as e:
            return f'Erro: {e}'

    def editar_produto(self, id_produto, coluna_editada: str, dado_editado):
        try:
            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')
            if id_produto in df['codigo'].values:
                if coluna_editada in df.columns:
                    df.loc[df["codigo"] == id_produto, coluna_editada] = dado_editado
                    df.to_csv(self.produtos_data, index=False, encoding='utf-8')
                else:
                    return 'Coluna não localizada'
            else:
                return 'Id não localizado'

        except Exception as e:
            return f"Erro ao editar: {e}"

    def busca_produto(self, coluna, dado_busca):
        try:
            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')
            if dado_busca in df.values:
                if coluna in df.columns:
                    busca = df[df[coluna] == dado_busca]
                    resultado = []
                    for _, row in busca.iterrows():
                        resultado.append(self.produto_model.formato(row))
                    return '\n'.join(resultado)
                else:
                    return 'Coluna não localizada'
            else:
                return 'Produto não localizado'
        except Exception as e:
            return f'Erro ao buscar: {e}'

    def deletar_produto(self, idbusca):
        try:
            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')

            if idbusca in df['codigo'].values:
                df = df[df['codigo'] != idbusca]
                df.to_csv(self.produtos_data, index=False)
                return 'Item deletado da base de dados!'
            else:
                return 'Codigo não localizado na base de dados'

        except Exception as e:
            return f'Falha ao deletar: {e}'

    def filtro_categoria(self, categoria):
        try:
            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')
            df_filtrado = df[df['categoria'] == categoria]

            if df_filtrado.empty:
                return f"Nenhum produto encontrado na categoria: {categoria}"

            resultado = []

            for _, row in df[df['categoria'] == categoria].iterrows():
                resultado.append(self.produto_model.formato(row))

            return "\n".join(resultado)

        except Exception as e:
            return f'Erro ao filtrar: {e}'

    def total_produtos(self):
        df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')
        total_cadastrado = df['codigo'].nunique()
        return f'Total de produtos cadastrados: {total_cadastrado}'

    def produtos_categoria(self):
        df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')
        total_categoria = df['categoria'].value_counts()
        linha = [f'{cat} : {qtd} Produtos' for cat, qtd in total_categoria.items()]
        return 'Quantidade por categoria:\n' + '\n'.join(linha)
