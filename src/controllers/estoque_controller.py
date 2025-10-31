from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
from src.utils.logKit.config_logging import get_logger
from src.config import PRODUTOS_DATA


class EstoqueController:
    def __init__(self):
        self.estoque_data = PRODUTOS_DATA
        self.estoque_log = get_logger("LoggerEstoqueController", "DEBUG")
        self.reservas = {}

    def _carregar_estoque(self) -> pd.DataFrame:
        """Metodo auxiliar para carregar estoque"""
        return pd.read_csv(self.estoque_data, encoding='utf-8', sep=',')

    def _salvar_estoque(self, df: pd.DataFrame) -> None:
        """Metodo auxiliar para salvar estoque"""
        df.to_csv(self.estoque_data, encoding='utf-8', sep=',', index=False)

    def _limpar_reservas_expiradas(self) -> None:
        """Remove reservas que expiraram"""
        agora = datetime.now()
        produtos_expirados = [
            produto_id for produto_id, dados in self.reservas.items()
            if dados.get("expira_em") and dados["expira_em"] < agora
        ]

        for produto_id in produtos_expirados:
            qtd_liberada = self.reservas[produto_id]["quantidade"]
            del self.reservas[produto_id]
            self.estoque_log.info(
                f"Reserva expirada automaticamente: Produto {produto_id}" f"{qtd_liberada} unidades liberadas")

    def reposicao(self, id_item: int, qtd: int) -> str:
        """Adiciona quantidade ao estoque"""
        try:
            self.estoque_log.debug(f"Repondo produto {id_item} Quantidade {qtd}")

            if qtd <= 0:
                self.estoque_log.warning("Quantidade menor/igual a zero")
                return "Quantidade menor ou igual a zero, sem possibilidade de reposição"

            df = self._carregar_estoque()

            if id_item not in df['codigo'].values:
                self.estoque_log.warning("Codigo não localizado")
                return "id não localizado"

            idx = df[df['codigo'] == id_item].index[0]
            nome_produto = df.loc[idx, 'nome']
            qtd_anterior = df.loc[idx, 'quantidade_estoque']

            df.loc[idx, 'quantidade_estoque'] += qtd
            self._salvar_estoque(df)
            self.estoque_log.info(f"Produto {nome_produto}: {qtd_anterior} -> {qtd_anterior + qtd} unidades")

            return f"Estoque do item {nome_produto} reposto"

        except Exception as e:
            self.estoque_log.exception("Erro ao repor estoque")
            return f'Erro: {e}'

    def produto_habilitado(self, id_produto: int) -> tuple[bool, str]:
        """Verifica se produto esta habilitado"""
        try:

            self.estoque_log.debug(f"Verificando se produto {id_produto} esta habilitado")
            df = self._carregar_estoque()

            if id_produto not in df['codigo'].values:
                self.estoque_log.warning(f"Produto: {id_produto} não localizado")
                return False, "Produto não localizado"

            idx = df['codigo'] == id_produto
            habilitado = df.loc[idx, 'ativo'].values[0]
            nome_produto = df.loc[idx, 'nome'].values[0]

            if not habilitado:
                self.estoque_log.warning(f"Produto: {nome_produto} desabilitado para uso")
                return False, f"Produto: {nome_produto} desabilitado"

            self.estoque_log.info(f"Produto: {nome_produto} Habilitado em estoque")
            return True, f'Produto: {nome_produto} Habilitado'

        except Exception as e:
            self.estoque_log.exception("Erro ao verificar produto")
            return False, f'Erro: {e}'

    def verificar_disponibilidade(self, produto_id: int, quantidade: int) -> tuple[bool, int]:
        """
        Verifica disponibilidade real considerando reservas

        Returns:
            (disponível: bool, quantidade_disponivel: int)
        """
        try:
            self._limpar_reservas_expiradas()
            df = self._carregar_estoque()
            if produto_id not in df['codigo'].values:
                return False, 0

            estoque_real = int(df.loc[df['codigo'] == produto_id, 'quantidade_estoque'].values[0])
            reservado = self.reservas.get(produto_id, {}).get("quantidade", 0)
            disponivel = estoque_real - reservado

            return disponivel >= quantidade, disponivel
        except Exception as e:
            self.estoque_log.exception("Erro ao verificar disponibilidade")
            return False, 0

    def reservar_estoque(self, produto_id: int, quantidade: int) -> bool:
        """
        Reserva estoque temporariamente (para carrinho)
        Reserva expira em 30 minutos
        """
        try:
            self.estoque_log.debug(f"Tentando reservar {quantidade} unidade do produto {produto_id}")

            if quantidade <= 0:
                self.estoque_log.warning("Quantidade inválida para reserva")
                return False

            self._limpar_reservas_expiradas()
            df = self._carregar_estoque()

            if produto_id not in self.reservas:
                self.reservas[produto_id] = {'quantiade': 0, 'expira_em': None}

            estoque_real = df.loc[df['codigo'] == produto_id, 'quantidade_estoque'].values[0]
            reservado = self.reservas[produto_id]['quantidade']
            disponivel = estoque_real - reservado

            if disponivel >= quantidade:
                self.reservas[produto_id] = {'quantidade': reservado + quantidade,
                                             'expira_em': datetime.now() + timedelta(minutes=30)}
                self.estoque_log.info(
                    f"Reserva confirmada: {quantidade} unidades do produto {produto_id} "
                    f"(disponível: {disponivel}, expira em 30min)"
                )
                return True

            self.estoque_log.warning(
                f"Reserva negada: Produto {produto_id} - Solicitado: {quantidade}, "
                f"Disponível: {disponivel}"
            )
            return False
        except Exception as e:
            self.estoque_log.exception(f"Erro ao reservar produto {produto_id}")
            return False

    def liberar_reserva(self, produto_id: int, quantidade: int):
        """Libera reserva de estoque (item removido do carrinho)"""
        try:
            if produto_id not in self.reservas:
                self.estoque_log.warning(f"Produto {produto_id} não tem reservas ativas")
                return "Sem reservas para liberar"

            self.reservas[produto_id]["quantidade"] -= quantidade

            if self.reservas[produto_id]['quantidade'] <= 0:
                del self.reservas[produto_id]
                self.estoque_log.info(f"Todas as reservas do produto {produto_id} foram liberadas")
            else:
                self.estoque_log.info(f"Reserva liberada: {quantidade} unidades do produto {produto_id}")

                return "Reserva liberada"

        except Exception as e:
            self.estoque_log.exception(f"Erro ao liberar reserva do produto {produto_id}")
            return f"Erro: {e}"

    def saida_estoque(self, id_produto: int, quantidade: int) -> tuple[bool, str]:
        """
        Realiza baixa real no estoque (venda finalizada)
        Também libera a reserva correspondente
        """
        try:
            df = self._carregar_estoque()

            if id_produto not in df['codigo'].values:
                self.estoque_log.error(f"Produto {id_produto} não encontrado para saida")
                return False, "Produto não encontrado"

            idx = df[df['codigo'] == id_produto].index[0]
            nome_produto = df.loc[idx, 'nome']
            estoque_atual = int(df.loc[idx, 'quantidade_estoque'].values[0])

            if estoque_atual < quantidade:
                self.estoque_log.error(
                    f"ERRO CRÍTICO: Tentativa de saída maior que estoque! "
                    f"Produto: {nome_produto} (ID: {id_produto}), "
                    f"Estoque atual: {estoque_atual}, Solicitado: {quantidade}"
                )
                return False, "Estoque insuficiente (erro crítico - contate o suporte)"

            df.loc[idx, 'quantidade_estoque'] -= quantidade
            self._salvar_estoque(df)

            self.liberar_reserva(id_produto, quantidade)
            self.estoque_log.info(
                f"Saída de estoque: {nome_produto} (ID: {id_produto}) - "
                f"{quantidade} unidades | Estoque: {estoque_atual} → {estoque_atual - quantidade}"
            )

            return True, f"Saída realizada: {quantidade} unidades de '{nome_produto}'"

        except Exception as e:
            self.estoque_log.exception("Erro ao realizar saida de estoque")
            return False, f'Erro: {e}'

    def obter_info_reservas(self, produto_id: Optional[int] = None) -> dict:
        """
        Retorna informações sobre reservas (útil para debug/dashboard)

        Args:
            produto_id: Se fornecido, retorna info apenas desse produto
        """
        self._limpar_reservas_expiradas()

        if produto_id:
            if produto_id in self.reservas:
                return {
                    produto_id: {
                        "quantidade": self.reservas[produto_id]["quantidade"],
                        "expira_em": self.reservas[produto_id]["expira_em"].isoformat()
                    }
                }
            return {}
        return {
            pid: {
                "quantidade": dados["quantidade"],
                "expira_em": dados["expira_em"].isoformat() if dados["expira_em"] else None
            }
            for pid, dados in self.reservas.items()
        }

