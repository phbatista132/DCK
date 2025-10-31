import pandas as pd
from datetime import datetime
from src.models.vendas import Venda, ItemVenda
from src.controllers import EstoqueController, ClienteController
from src.utils.file_helpers import gerar_arquivo, verificar_arquivo_vazio
from src.utils.logKit.config_logging import get_logger
from src.config import PRODUTOS_DATA, VENDAS_DIR, ITENS_VENDAS_DIR


class VendaController:
    def __init__(self):
        self.carrinho = []
        self.vendas_log = get_logger("LoggerVendasController", "DEBUG")
        self.estoque = EstoqueController()
        self.cliente = ClienteController()
        self.estoque_data = PRODUTOS_DATA
        self.vendas_data = VENDAS_DIR
        self.itens_venda_data = ITENS_VENDAS_DIR

    def venda_id(self) -> int:
        """Gera ID único para venda"""
        id_venda = 1
        if not verificar_arquivo_vazio(self.vendas_data):
            try:
                df_existente = pd.read_csv(self.vendas_data, encoding='utf-8', sep=',')
                if 'id_venda' in df_existente.columns and not df_existente['id_venda'].empty and not df_existente[
                    'id_venda'].isna().all():
                    id_venda = int(df_existente['id_venda'].max()) + 1

            except Exception as e:
                self.vendas_log.exception(f"Erro ao gerar a codigo: {e}")

        return id_venda

    def adicionar_item(self, produto_id: int, quantidade: int):
        try:
            self.vendas_log.debug(f"Adicionando item {produto_id} - {quantidade}")
            df = pd.read_csv(self.estoque_data, encoding="utf-8", sep=",")

            if produto_id not in df['codigo'].values:
                self.vendas_log.warning(f"Produto {produto_id} não encontrado")
                return "Produto não encontrado"

            idx = df["codigo"] == produto_id
            preco_unitario = df.loc[idx, 'valor'].values[0]
            nome_produto = df.loc[idx, 'nome'].values[0]

            habilitado, msg = self.estoque.produto_habilitado(produto_id)
            if not habilitado:
                self.vendas_log.warning(f"Produto: {nome_produto} desabilitado")
                return msg

            if not self.estoque.reservar_estoque(produto_id, quantidade):
                self.vendas_log.warning(f"Quantidade: {quantidade} indisponivel")
                return "Quantidade indisponivel"

            item = {
                "produto_id": produto_id,
                "nome": nome_produto,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "subtotal": preco_unitario * quantidade

            }
            self.carrinho.append(item)
            self.vendas_log.debug(f"Item adicionado ao carrinho: {item}")

            return "Item adicionado ao carrinho"
        except Exception as e:
            self.vendas_log.exception(f"Erro ao adicionar produto {produto_id}")
            return f"Erro: {e}"

    def ver_carinho(self):
        """Retorna carrinho atual"""
        return self.carrinho

    def remover_item(self, produto_id: int):
        """Remove item do carrinho"""
        try:
            self.vendas_log.debug(f"Removendo item: {produto_id} do carrinho")

            item = next((i for i in self.carrinho if i['produto_id'] == produto_id), None)
            if not item:
                self.vendas_log.warning(f"Produto: {produto_id} não está no carrinho")
                return f"Item não encotrado no carrinho"

            self.estoque.liberar_reserva(item['produto_id'], item['quantidade'])

            self.carrinho.remove(item)

            self.vendas_log.info(f"Item removido do carrinho: {item['nome']} - Reserva liberada")
            return "Item removido do carrinho"
        except Exception as e:
            self.vendas_log.exception(f"Erro ao remover item {produto_id}")
            return f"Erro: {e}"

    def alterar_quantidade(self, produto_id: int, nova_quantidade: int):
        """Altera quantidade de um item no carrinho"""
        try:
            self.vendas_log.debug(f"Alterando quantidade do item: {produto_id}")

            if nova_quantidade <= 0:
                return "Quantidade deve ser maior que zero"

            item = next((i for i in self.carrinho if i['produto_id'] == produto_id), None)

            if not item:
                self.vendas_log.warning(f"Produto {produto_id} não esta no carrinho")
                return "Item não encontrado no carrinho"

            quantidade_atual = item['quantidade']
            diferenca = nova_quantidade - quantidade_atual

            if diferenca > 0:
                if not self.estoque.reservar_estoque(produto_id, diferenca):
                    self.vendas_log.warning(f"Estoque insuficiente para aumentar quantidade: {nova_quantidade}")
                    return "Estoque insuficiente"

            elif diferenca < 0:
                self.estoque.liberar_reserva(produto_id, abs(diferenca))

            item['quantidade'] = nova_quantidade
            item['subtotal'] = item['preco_unitario'] * nova_quantidade

            self.vendas_log.info(f"Quantidade alterada: {quantidade_atual} → {nova_quantidade}")
            return "Quantidade alterada com sucesso"

        except Exception as e:
            self.vendas_log.exception(f"Erro ao alterar quantidade")
            return f"Erro: {e}"

    def _calcular_subtotal(self) -> float:
        """Calcular subtotal do carrinho"""
        return sum(item["subtotal"] for item in self.carrinho)



    def finalizar_venda(self, cpf_cliente: str = None, forma_pagamento: str = "Debito", percentual_desconto: float = 0):
        """
                Finaliza venda criando objeto Venda e persistindo

        Args:
            cpf_cliente: CPF do cliente (opcional)
            forma_pagamento: Forma de pagamento
            percentual_desconto: Desconto percentual (0-100)
        """
        try:
            gerar_arquivo(self.vendas_data)
            gerar_arquivo(self.itens_venda_data)

            if not self.carrinho:
                self.vendas_log.warning("Carinho de compras vazio")
                return "Carrrinho vazio"

            cliente_id = None
            if cpf_cliente:
                cliente = self.cliente.buscar_cliente(cpf=cpf_cliente)
                if isinstance(cliente, dict):
                    if not cliente.get('status', False):
                        self.vendas_log.warning(f"Cliente {cpf_cliente} está inativo")
                        return "Cliente inativo, sem possibilidade de vincular compra"
                    cliente_id = cliente['id_cliente']
                else:
                    self.vendas_log.warning(f"Cliente {cpf_cliente} não encontrado")
                    return "Cliente não encontrado"


            itens_venda = [
                ItemVenda(produto_id=item['produto_id'], nome_produto=item['nome'],
                          quantidade=item['quantidade'], preco_unitario=item['preco_unitario'],
                          subtotal=item['subtotal'])
                for item in self.carrinho
            ]

            venda = Venda(
                id_venda=self.venda_id(), data_hora=datetime.now(), itens=itens_venda, subtotal=self._calcular_subtotal(),
                desconto=0.0, total=0.0, forma_pagamento=forma_pagamento, cliente_id=cliente_id
            )

            if percentual_desconto > 0:
                try:
                    venda.aplicar_desconto(percentual_desconto)
                    self.vendas_log.info(f"Desconto aplicado: {percentual_desconto}")
                except ValueError as e:
                    self.vendas_log.exception("Erro ao aplicar desconto")
                    return f"Erro no desconto: {e}"



            df_venda = pd.DataFrame([venda.to_dict()])
            arquivo_vazio = verificar_arquivo_vazio(self.vendas_data)
            df_venda.to_csv(self.vendas_data, mode='a', header=arquivo_vazio, index=False, sep=',')

            for item in self.carrinho:
                self.estoque.saida_estoque(item['produto_id'], item['quantidade'])

            self.carrinho.clear()

            self.vendas_log.info(f"Venda {venda.id_venda} finalizada | Total: {venda.total}")

            return f"Compra finalizada! ID: {venda.id_venda} | Total: R$ {venda.total:.2f}"
        except ValueError as ve:
            self.vendas_log.error(f"Erro de validação: {ve}")
            return f"Erro de validação: {ve}"
        except Exception as e:
            self.vendas_log.exception(f"Erro ao finalizar venda: {e}")
            return f"Erro: {e}"

    def cancelar_venda(self) -> str:
        """Cancela venda atual e libera todas as reservas"""
        try:
            if not self.carrinho:
                return "Carrrinho se encontra vazio"

            for item in self.carrinho:
                self.estoque.liberar_reserva(item['produto_id'], item['quantidade'])

            self.carrinho.clear()
            self.vendas_log.info("Venda cancelada - Todas as reservas foram liberadas")

            return "Venda cancelada com sucesso"

        except Exception as e:
            self.vendas_log.exception(f"Erro ao cancelar venda")
            return f"Erro: {e}"
