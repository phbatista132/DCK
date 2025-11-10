import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from src.models.vendas import Venda, ItemVenda
from src.controllers import EstoqueController, ClienteController
from src.utils.file_helpers import gerar_arquivo, verificar_arquivo_vazio
from src.utils.logKit.config_logging import get_logger
from src.config import PRODUTOS_DATA, VENDAS_DIR, ITENS_VENDAS_DIR


class VendaController:
    def __init__(self):
        self.carrinhos: Dict[int, List[dict]] = {}
        self.vendas_log = get_logger("LoggerVendasController", "DEBUG")
        self.estoque = EstoqueController()
        self.cliente = ClienteController()
        self.estoque_data = PRODUTOS_DATA
        self.vendas_data = VENDAS_DIR
        self.itens_venda_data = ITENS_VENDAS_DIR

    def _get_carrinho(self, user_id: int):
        """Carrinho do usuario especifico"""

        if user_id not in self.carrinhos:
            self.carrinhos[user_id] = []
        return self.carrinhos[user_id]

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

    def adicionar_item(self, produto_id: int, quantidade: int, user_id: int):
        """
        Adiciona item ao carrinho do usuário específico

        Args:
            produto_id: ID do produto
            quantidade: Quantidade desejada
            user_id: ID do usuário autenticado

        """
        try:
            self.vendas_log.debug(f"Adicionando item {produto_id} - {quantidade}")
            df = pd.read_csv(self.estoque_data, encoding="utf-8", sep=",")

            if produto_id not in df['codigo'].values:
                self.vendas_log.warning(f"Produto {produto_id} não encontrado")
                return "Produto não encontrado"

            idx = df[df["codigo"] == produto_id].index[0]
            preco_unitario = df.loc[idx, 'valor']
            nome_produto = df.loc[idx, 'nome']

            habilitado, msg = self.estoque.produto_habilitado(produto_id)
            if not habilitado:
                self.vendas_log.warning(f"Produto: {nome_produto} desabilitado")
                return msg

            if not self.estoque.reservar_estoque(produto_id, quantidade):
                self.vendas_log.warning(f"Quantidade: {quantidade} indisponivel")
                return "Quantidade indisponivel"

            carrinho = self._get_carrinho(user_id)

            item_existente = next((i for i in carrinho if i['produto_id'] == produto_id), None)

            if item_existente:
                item_existente['quantidade'] += quantidade
                item_existente['subtotal'] = item_existente['preco_unitario'] * item_existente['quantidade']
                self.vendas_log.info(f"Quantidade atualizada no carrinho do user {user_id}")
            else:
                item = {
                    "produto_id": produto_id,
                    "nome": nome_produto,
                    "quantidade": quantidade,
                    "preco_unitario": preco_unitario,
                    "subtotal": preco_unitario * quantidade

                }
                carrinho.append(item)
                self.vendas_log.debug(f"Item adicionado ao carrinho: {item}")

            return "Item adicionado ao carrinho"
        except Exception as e:
            self.vendas_log.exception(f"Erro ao adicionar produto {produto_id}")
            return f"Erro: {e}"

    def ver_carinho(self, user_id: int):
        """Retorna carrinho atual"""
        self._get_carrinho(user_id)

    def remover_item(self, produto_id: int, user_id: int):
        """Remove item do carrinho do usuário"""
        try:
            carrinho = self._get_carrinho(user_id)

            item = next((i for i in carrinho if i['produto_id'] == produto_id), None)
            if not item:
                self.vendas_log.warning(f"Produto: {produto_id} não está no carrinho do user {user_id}")
                return f"Item não encotrado no carrinho"

            self.estoque.liberar_reserva(item['produto_id'], item['quantidade'])
            carrinho.remove(item)

            self.vendas_log.info(f"Item removido do carrinho do user {user_id}: {item['nome']}")
            return "Item removido do carrinho"

        except Exception as e:
            self.vendas_log.exception(f"Erro ao remover item {produto_id}")
            return f"Erro: {e}"

    def alterar_quantidade(self, produto_id: int, nova_quantidade: int, user_id: int):
        """Altera quantidade no carrinho do usuário"""
        try:
            if nova_quantidade <= 0:
                return "Quantidade deve ser maior que zero"

            carrinho = self._get_carrinho(user_id)
            item = next((i for i in carrinho if i['produto_id'] == produto_id), None)

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

            self.vendas_log.info(f"user {user_id} Quantidade alterada: {quantidade_atual} → {nova_quantidade}")
            return "Quantidade alterada com sucesso"

        except Exception as e:
            self.vendas_log.exception(f"Erro ao alterar quantidade")
            return f"Erro: {e}"

    def _calcular_subtotal(self, carrinho: List[dict]) -> float:
        """Calcular subtotal do carrinho"""
        return sum(item["subtotal"] for item in carrinho)

    def finalizar_venda(self, cpf_cliente: str = None, forma_pagamento: str = "Debito", percentual_desconto: float = 0,
                        user_id: Optional[int] = None, username: Optional[str] = None):
        """
                Finaliza venda criando objeto Venda e persistindo

        Args:
            cpf_cliente: CPF do cliente (opcional)
            forma_pagamento: Forma de pagamento
            percentual_desconto: Desconto percentual (0-100)
            user_id: Id do usuario
            username: Nome do usuario
        """
        try:
            gerar_arquivo(self.vendas_data)
            gerar_arquivo(self.itens_venda_data)

            if user_id is None:
                return "Erro: ID do vendedor não fornecido"

            carrinho = self._get_carrinho(user_id)

            if not carrinho:
                self.vendas_log.warning(f"Carrinho vazio do user {user_id}")
                return "Carrrinho vazio"

            cliente_id = None
            if cpf_cliente:
                cliente = self.cliente.buscar_cliente(cpf=cpf_cliente)

                if cliente is None:
                    self.vendas_log.warning(f"Cliente {cpf_cliente} não encontrado")
                    return "Cliente não encontrado"

                if not getattr(cliente, 'ativo', False):
                    self.vendas_log.warning(f"Cliente {cpf_cliente} está inativo")
                    return "Cliente inativo, sem possibilidade de vincular compra"

                cliente_id = cliente.id_cliente

            itens_venda = [
                ItemVenda(produto_id=item['produto_id'], nome_produto=item['nome'],
                          quantidade=item['quantidade'], preco_unitario=item['preco_unitario'],
                          subtotal=item['subtotal'])
                for item in carrinho
            ]

            venda = Venda(
                id_venda=self.venda_id(), data_hora=datetime.now(), itens=itens_venda,
                subtotal=self._calcular_subtotal(carrinho),
                desconto=0.0, total=0.0, forma_pagamento=forma_pagamento, cliente_id=cliente_id,
                vendedor_id=user_id,vendedor_nome=username
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

            for item in carrinho:
                self.estoque.saida_estoque(item['produto_id'], item['quantidade'])

            carrinho.clear()

            self.vendas_log.info(f"Venda {venda.id_venda} finalizada por {username} (ID: {user_id}) ")
            return f"Compra finalizada! ID: {venda.id_venda} | Total: R$ {venda.total:.2f}"

        except ValueError as ve:
            self.vendas_log.error(f"Erro de validação: {ve}")
            return f"Erro de validação: {ve}"
        except Exception as e:
            self.vendas_log.exception(f"Erro ao finalizar venda: {e}")
            return f"Erro: {e}"

    def cancelar_venda(self, user_id) -> str:
        """Cancela venda atual e libera todas as reservas"""
        try:
            carrinho = self._get_carrinho(user_id)
            if not carrinho:
                return "Carrrinho se encontra vazio"

            for item in carrinho:
                self.estoque.liberar_reserva(item['produto_id'], item['quantidade'])

            carrinho.clear()
            self.vendas_log.info(f"Venda cancelada pelo user {user_id} - Reservas liberadas")

            return "Venda cancelada com sucesso"

        except Exception as e:
            self.vendas_log.exception(f"Erro ao cancelar venda")
            return f"Erro: {e}"
