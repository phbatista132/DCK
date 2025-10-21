import os
import pandas as pd
from datetime import date
from src.models.produto import Produto
from src.utils.logKit.config_logging import get_logger
from src.utils.file_helpers import gerar_arquivo, verificar_aquivo_vazio
from src.config import PRODUTOS_DATA


def data_cadastro():
    return date.today()


def duplicado(arquivo, nome, modelo, categoria) -> bool:
    df = pd.read_csv(arquivo, encoding='utf-8', sep=',')
    duplicada = df[(df['nome'] == nome) &
                   (df['modelo'] == modelo) &
                   (df['categoria'] == categoria)]
    return duplicada.empty


class ProdutoController:
    def __init__(self, produtos_data=PRODUTOS_DATA):
        self.produto_model = Produto()
        self.produtos_data = produtos_data
        self.produto_log = get_logger("LoggerProdutoController", "DEBUG")

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
                self.produto_log.exception(f"Erro ao gerar a codigo: {e}")

        return codigo

    def cadastrar_produto(self, nome, modelo, categoria, valor: float, quantidade_estoque: int, vlr_compra: float):
        try:
            gerar_arquivo(self.produtos_data)

            if not self.produto_model.validar_dados(valor, vlr_compra, quantidade_estoque):
                self.produto_log.warning(f"Validacao falhou para o produto: {nome}")
                return "Dados Invalidos"

            if not duplicado(self.produtos_data, nome, modelo, categoria):
                self.produto_log.warning(f"Produto {nome} ja existe")
                return "Produto ja cadastrado"

            codigo = self.gera_codigo()
            self.produto_model.dados(nome, modelo, categoria, valor, codigo, quantidade_estoque,
                                     data_cadastro(), vlr_compra, self.produto_model.margem_lucro(valor, vlr_compra))
            self.produto_log.debug("Dados para cadastro recebido")

            salvar_produto = pd.DataFrame(self.produto_model.produtos)
            arquivo_vazio = verificar_aquivo_vazio(self.produtos_data)

            salvar_produto.to_csv(self.produtos_data, mode='a', header=arquivo_vazio, index=False, sep=',',
                                  encoding='utf-8')
            self.produto_model.produtos.clear()
            self.produto_log.info("Produto %s cadastrado com sucesso.", nome)
            return f"Produto cadastrado com sucesso"

        except Exception as e:
            self.produto_log.exception(f'Erro: {e}')
            return f'Erro: {e}'


    def editar_produto(self, id_produto, coluna_editada: str, dado_editado):
        try:
            self.produto_log.debug(f"Editando produto {id_produto}, coluna {coluna_editada}")

            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')

            if id_produto not in df['codigo'].values:
                self.produto_log.warning(f"Produto {id_produto} não encontrado")
                return 'Id não localizado'

            if coluna_editada not in df.columns:
                self.produto_log.warning(f"Coluna '{coluna_editada}' não existe")
                return 'Coluna não localizada'

            df.loc[df["codigo"] == id_produto, coluna_editada] = dado_editado
            df.to_csv(self.produtos_data, index=False, encoding='utf-8', sep=',')

            self.produto_log.info(f"Produto {id_produto} editado: {coluna_editada}='{dado_editado}'")
            return "Produto editado com sucesso"

        except Exception as e:
            self.produto_log.exception(f'Erro ao editar produto {id_produto}')
            return f"Erro ao editar: {e}"


    def busca_produto(self, coluna, dado_busca):
        try:
            self.produto_log.debug(f"Filtrando coluna: {coluna} - Buscando dado {dado_busca}")
            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')

            if coluna not in df.columns:
                self.produto_log.warning(f"Coluna {coluna} não existe")
                return "Coluna não localizada"

            busca = df[df[coluna] == dado_busca]

            if busca.empty:
                self.produto_log.warning(f"Dado: {dado_busca} não localizado")
                return "Dado não localizado"

            resultado = []
            for _, row in busca.iterrows():
                resultado.append(self.produto_model.formato(row))

            self.produto_log.info(f"Encontrado {len(resultado)} produtos")
            return '\n'.join(resultado)

        except Exception as e:
            self.produto_log.exception(f"Erro ao localizar dado '{dado_busca}'")
            return f'Erro ao buscar: {e}'

    def desabilitar_produto(self, idbusca):
        try:
            self.produto_log.debug(f"Desativando produto {idbusca}")
            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')

            if idbusca not in df['codigo'].values:
                self.produto_log.warning(f"Produto: {idbusca} não localizado")
                return "Produto não encontrado"

            produto_nome = df[df['codigo'] == idbusca]['nome'].values[0]

            df.loc[df["codigo"] == idbusca, 'ativo'] = False

            df.to_csv(self.produtos_data, encoding='utf-8', sep=',', index=False)
            self.produto_log.info(f"Produto {idbusca} ({produto_nome}) desativado")
            return "Produto desativado com sucesso"

        except Exception as e:
            self.produto_log.exception(f"Erro ao deletar produto: {idbusca}")
            return f'Falha ao desativar: {e}'


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
        self.produto_log.info(f"Total de produtos: {total_cadastrado}")
        return f'Total de produtos cadastrados: {total_cadastrado}'


    def produtos_categoria(self):
        df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')
        total_categoria = df['categoria'].value_counts()
        linha = [f'{cat} : {qtd} Produtos' for cat, qtd in total_categoria.items()]
        return 'Quantidade por categoria:\n' + '\n'.join(linha)
