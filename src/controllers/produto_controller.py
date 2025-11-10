import os
import pandas as pd
from typing import List
from datetime import date
from src.models.produto import Produto
from src.utils.logKit.config_logging import get_logger
from src.utils.file_helpers import gerar_arquivo, verificar_arquivo_vazio, duplicado
from src.config import PRODUTOS_DATA


class ProdutoController:
    def __init__(self):
        self.produto_model = Produto
        self.produtos_data = PRODUTOS_DATA
        self.produto_log = get_logger("LoggerProdutoController", "DEBUG")

    def _carregar_produtos(self) -> pd.DataFrame:
        return pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')

    def _salvar_produtos(self, df: pd.DataFrame, mode: str = 'w') -> None:
        """
        Salva produtos no CSV

        Args:
        df: DataFrame com produtos
        mode: 'w' = sobrescrever, 'a' = adicionar (append)
        """
        arquivo_vazio = verificar_arquivo_vazio(self.produtos_data)

        header = arquivo_vazio if mode == 'a' else True

        df.to_csv(self.produtos_data, mode=mode, encoding='utf-8', sep=',', index=False, header=header)

    def gera_codigo(self) -> int:
        codigo = 1
        if os.path.isfile(self.produtos_data) and os.path.getsize(self.produtos_data) > 0:
            try:
                df = self._carregar_produtos()
                if 'codigo' in df.columns and not df['codigo'].empty and not df[
                    'codigo'].isna().all():
                    codigo = int(df['codigo'].max()) + 1
                else:
                    codigo = 1

            except Exception as e:
                self.produto_log.exception(f"Erro ao gerar a codigo: {e}")

        return codigo

    def cadastrar_produto(self, nome: str, modelo: str, categoria: str, valor: float, quantidade_estoque: int,
                          vlr_compra: float) -> str:
        try:
            gerar_arquivo(self.produtos_data)
            if valor <= 0:
                self.produto_log.warning("Valor de venda inválido")
                return "Valor de venda deve ser maior que zero"

            if vlr_compra <= 0:
                self.produto_log.warning("Valor de compra inválido")
                return "Valor de compra deve ser maior que zero"

            if quantidade_estoque < 0:
                self.produto_log.warning("Quantidade inválida")
                return "Quantidade de estoque não pode ser negativa"

            if valor <= vlr_compra:
                self.produto_log.warning("Margem de lucro negativa")
                return "Valor de venda deve ser maior que valor de compra"

            arquivo_vazio = verificar_arquivo_vazio(self.produtos_data)
            if not arquivo_vazio:
                if duplicado(self.produtos_data, nome=nome, modelo=modelo, categoria=categoria):
                    self.produto_log.warning(f"Produto {nome} ja existe")
                    return "Produto ja cadastrado"

            codigo = self.gera_codigo()
            produto = Produto(
                codigo=codigo,
                nome=nome,
                modelo=modelo,
                categoria=categoria,
                valor=valor,
                quantidade_estoque=quantidade_estoque,
                vlr_compra=vlr_compra,
                margem_lucro=0,
                dt_cadastro=date.today()
            )

            self._salvar_produtos(pd.DataFrame([produto.to_dict()]), mode='a')

            self.produto_log.info("Produto %s cadastrado com sucesso.", nome)
            return f"Produto cadastrado com sucesso"


        except ValueError as ve:
            self.produto_log.warning(f"Validação falhou: {ve}")
            return f"Dados inválidos: {ve}"
        except Exception as e:
            self.produto_log.exception("Erro ao cadastrar produto")
            return f'Erro: {e}'

    def editar_produto(self, id_produto, **kwargs) -> str:
        """
        Edita produto (whitelist: nome, modelo, categoria, valor, vlr_compra, quantidade_estoque)

        Uso:
            editar_produto(1, nome="Notebook Dell", valor=3500.0)
        """
        try:
            coluna_editaveis = ['nome', 'modelo', 'valor', 'vlr_compra']

            for coluna in kwargs.keys():
                if coluna not in coluna_editaveis:
                    self.produto_log.warning(f'Campo: {coluna} não permitido para edição')
                    return "Campo não pode ser editado"

            if 'valor' in kwargs and kwargs['valor'] <= 0:
                return "Valor de venda deve ser maior que zero"

            if 'vlr_compra' in kwargs and kwargs['vlr_compra'] <= 0:
                return "Valor de compra deve ser maior que zero"

            if 'quantidade_estoque' in kwargs and kwargs['quantidade_estoque'] < 0:
                return "Quantidade não pode ser negativa"

            df = self._carregar_produtos()

            if id_produto not in df['codigo'].values:
                self.produto_log.warning(f"Produto {id_produto} não encontrado")
                return 'Id não localizado'

            for coluna, valor in kwargs.items():
                df.loc[df["codigo"] == id_produto, coluna] = valor

            if 'valor' in kwargs or 'vlr_compra' in kwargs:
                idx = df[df['codigo'] == id_produto].index[0]
                valor_venda = float(df.loc[idx, 'valor'])
                valor_compra = float(df.loc[idx, 'vlr_compra'])

                if valor_compra > 0 and valor_venda < valor_compra:
                    margem = ((valor_venda - valor_compra) / valor_compra) * 100
                    df.loc[idx, 'margem_lucro'] = round(margem, 2)

            self._salvar_produtos(df, mode="w")

            self.produto_log.info(f"Produto {id_produto} editado: {kwargs} com sucesso")
            return "Produto editado com sucesso"

        except Exception as e:
            self.produto_log.exception(f'Erro ao editar produto {id_produto}')
            return f"Erro ao editar: {e}"

    def busca_produto(self, coluna:str, dado_busca: str)-> str | List:
        """Busca produtos por coluna e retorna string formatada"""
        try:
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
                linha = (
                    f"Produto: {row['nome']} | Modelo {row['modelo']} | Estoque: {row['quantidade_estoque']} | Valor: {row['valor']}"
                )
                resultado.append(linha)

            self.produto_log.info(f"Encontrado {len(resultado)} produtos")
            return resultado
        except Exception as e:
            self.produto_log.exception(f"Erro ao localizar dado '{dado_busca}'")
            return f'Erro ao buscar: {e}'

    def desabilitar_produto(self, idbusca: int) -> str:
        """Desativa produto (soft delete)"""
        try:
            df = self._carregar_produtos()

            if idbusca not in df['codigo'].values:
                self.produto_log.warning(f"Produto: {idbusca} não localizado")
                return "Produto não encontrado"

            produto_nome = df[df['codigo'] == idbusca]['nome'].values[0]

            df.loc[df["codigo"] == idbusca, 'ativo'] = False

            self._salvar_produtos(df, mode="w")
            self.produto_log.info(f"Produto {idbusca} ({produto_nome}) desativado")
            return "Produto desativado com sucesso"

        except Exception as e:
            self.produto_log.exception(f"Erro ao deletar produto: {idbusca}")
            return f'Falha ao desativar: {e}'

    def filtro_categoria(self, categoria) -> str:
        """Filtra produtos por categoria"""
        try:
            df = self._carregar_produtos()
            df_filtrado = df[(df['categoria'] == categoria) & df['ativo']]

            if df_filtrado.empty:
                return f"Nenhum produto encontrado na categoria: {categoria}"

            resultado = []

            for _, row in df_filtrado.iterrows():
                linha = (
                    f"Produto: {row['nome']} | Modelo: {row['modelo']} | "
                    f"Categoria: {row['categoria']} | Valor: R$ {row['valor']:.2f} | "
                    f"Estoque: {row['quantidade_estoque']}"
                )
                resultado.append(linha)

            self.produto_log.info(f"Encontrados {len(resultado)} produtos")
            return "\n".join(resultado)

        except Exception as e:
            self.produto_log.warning("Erro ao filtrar categoria")
            return f'Erro ao filtrar: {e}'

    def total_produtos(self) -> str:
        """Retorna total de produtos cadastrados"""
        try:
            df = self._carregar_produtos()
            total_cadastrado = df['codigo'].nunique()

            self.produto_log.info(f"Total de produtos: {total_cadastrado}")
            return f'Total de produtos cadastrados: {total_cadastrado}'
        except Exception as e:
            self.produto_log.exception(f"Erro ao contar produtos")
            return f'Erro: {e}'

    def produtos_categoria(self) -> str:
        """Retorna quantidade de produtos por categoria"""
        try:
            df = pd.read_csv(self.produtos_data, encoding='utf-8', sep=',')
            total_categoria = df['categoria'].value_counts()

            linha = [f'{cat} : {qtd} Produtos' for cat, qtd in total_categoria.items()]

            self.produto_log.info(f"Quantidade de produtos: {len(linha)}")
            return 'Quantidade por categoria:\n' + '\n'.join(linha)

        except Exception as e:
            self.produto_log.exception(f"Erro ao listar categorias")
            return f'Erro: {e}'
