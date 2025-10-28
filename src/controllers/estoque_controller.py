import pandas as pd
from src.models.produto import Produto
from src.utils.logKit.config_logging import get_logger
from src.config import PRODUTOS_DATA


class EstoqueController:
    def __init__(self):
        self.produto_estoque = Produto()
        self.estoque_data = PRODUTOS_DATA
        self.estoque_log = get_logger("LoggerEstoqueController", "DEBUG")
        self.reservas = {}

    def reposicao(self, id_item: int, qtd: int) -> str:
        try:
            self.estoque_log.debug(f"Repondo produto {id_item} Quantidade {qtd}")
            df = pd.read_csv(self.estoque_data, encoding='utf-8', sep=',')
            if id_item not in df['codigo'].values:
                self.estoque_log.warning("Codigo não localizado")
                return "id não localizado"

            if qtd <= 0:
                self.estoque_log.warning("Quantidade menor/igual a zero")
                return "Quantidade menor ou igual a zero, sem possibilidade de reposição"

            idx = df[df['codigo'] == id_item].index[0]
            nome_produto = df.loc[idx, 'nome']
            qtd_anterior = df.loc[idx, 'quantidade_estoque']

            df.loc[idx, 'quantidade_estoque'] += qtd
            df.to_csv(self.estoque_data, index=False, encoding='utf-8', sep=',')
            self.estoque_log.info(f"Produto {nome_produto}: {qtd_anterior} -> {qtd_anterior + qtd} unidades")

            return f"Estoque do item {nome_produto} reposto"

        except Exception as e:
            self.estoque_log.exception("Erro ao repor estoque")
            return f'Erro ao repor produto: {e}'

    def produto_habilitado(self, id_produto: int) -> tuple[bool, str]:
        try:

            self.estoque_log.debug(f"Verificando se produto {id_produto} esta habilitado")
            df = pd.read_csv(self.estoque_data, encoding='utf-8', sep=',')

            if id_produto not in df['codigo'].values:
                self.estoque_log.warning(f"Produto: {id_produto} não localizado")
                return False, "Produto não localizado"


            idx = df['codigo'] == id_produto
            habilitado = df.loc[idx, 'ativo'].values[0]
            nome_produto = df.loc[idx, 'nome'].values[0]

            if not habilitado :
                self.estoque_log.warning(f"Produto: {nome_produto} desabilitado para uso")
                return False, f"Produto: {nome_produto} desabilitado"

            self.estoque_log.info(f"Produto: {nome_produto} Habilitado em estoque")
            return True, f'Produto: {nome_produto} Habilitado'
        except Exception as e:
            self.estoque_log.exception("Erro ao verificar produto")
            return False, f'Erro: {e}'

    def reservar_estoque(self, produto: int, quantidade: int) -> bool:
        try:
            self.estoque_log.debug(f"Tentando reservar {quantidade} unidade do produto {produto}")
            if produto not in self.reservas:
                self.reservas[produto] = 0

            df = pd.read_csv(self.estoque_data, encoding='utf-8', sep=',')

            estoque_real = df.loc[df['codigo'] == produto, 'quantidade_estoque'].values[0]
            disponivel = estoque_real - self.reservas[produto]

            if disponivel > quantidade:
                self.reservas[produto] += quantidade
                self.estoque_log.info(
                    f"Reserva confirmada: {quantidade} unidades do produto {produto} (disponível: {disponivel})")
                return True

            self.estoque_log.warning(f"Reserva negada para o produto: {produto}")
            return False
        except Exception as e:
            self.estoque_log.exception(f"Erro ao reservar produto {produto}")
            return False

    def liberar_reserva(self, produto: int, quantidade: int):
        try:
            if produto in self.reservas:
                self.reservas[produto] -= quantidade

                if self.reservas[produto] < 0:
                    self.reservas[produto] = 0

                self.estoque_log.debug(f"Reserva liberada: {quantidade} unidades do produto {produto}")
                return "Reserva liberada"
        except Exception as e:
            self.estoque_log.exception(f"Erro ao liberar reserva do produto {produto}")
            return f"Erro: {e}"


    def saida_estoque(self, id_produto: int, quantidade: int):
        try:
            df = pd.read_csv(self.estoque_data, encoding='utf-8', sep=',')

            idx = df[df['codigo'] == id_produto].index[0]
            nome_produto = df.loc[idx, 'nome']
            df.loc[idx, 'quantidade_estoque'] -= quantidade

            self.liberar_reserva(id_produto, quantidade)

            df.to_csv(self.estoque_data, encoding='utf-8', sep=',', index=False)
            self.estoque_log.info(f"Saida de estoque: {nome_produto} - {quantidade}")

            return f"Saida de estoque realizada em: {quantidade}"

        except Exception as e:
            self.estoque_log.exception("Erro ao realizar saida de estoque")
            return f'Erro: {e}'


