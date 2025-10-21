import os.path
from src.models.vendas import Vendas
from src.config import PRODUTOS_DATA, VENDAS_DIR
from src.utils.logKit.config_logging import get_logger
from src.utils.file_helpers import gerar_arquivo, verificar_aquivo_vazio
from datetime import datetime
from src.controllers import EstoqueController
import pandas as pd


class VendaController:
    def __init__(self):
        self.vendas_model = Vendas()
        self.carrinho = []
        self.vendas_log = get_logger("LoggerVendasController", "DEBUG")
        self.estoque = EstoqueController()
        self.estoque_data = PRODUTOS_DATA
        self.vendas_data = VENDAS_DIR

    def venda_id(self) -> int:
        id_venda = 1
        if os.path.isfile(self.vendas_data) and os.path.getsize(self.vendas_data) > 0:
            try:
                df_existente = pd.read_csv(self.vendas_data, encoding='utf-8', sep=',')
                if 'id_venda' in df_existente.columns and not df_existente['id_venda'].empty and not df_existente[
                    'id_venda'].isna().all():
                    id_venda = int(df_existente['id_venda'].max()) + 1
                else:
                    id_venda = 1

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
        return self.carrinho

    def remover_item(self, produto_id: int):
        try:
            self.vendas_log.debug(f"Removendo item: {produto_id} do carrinho")

            item = None
            for i in self.carrinho:
                if i["produto_id"] == produto_id:
                    item = i
                    break

            if not item:
                self.vendas_log.warning(f"Produto: {produto_id} não está no carrinho")
                return f"Item não encotrado no carrinho"

            self.estoque.liberar_reserva(item['codigo'], item['quantidade'])

            self.carrinho.remove(item)

            self.vendas_log.info(f"Item removido do carrinho: {item['nome']} - Reserva liberada")
            return "Item removido do carrinho"
        except Exception as e:
            self.vendas_log.exception(f"Erro ao remover item {produto_id}")
            return f"Erro: {e}"



    def total_compra(self):
        total = []
        for item in self.carrinho:
            total.append(item["subtotal"])

        return sum(total)

    def finalizar_venda(self, client_id: int | None, forma_pagamento="Debito", desconto=0):
        try:
            gerar_arquivo(self.vendas_data)

            if not self.carrinho:
                self.vendas_log.warning("Carinho de compras vazio")
                return "Carrrinho vazio"

            codigo = self.venda_id()
            self.vendas_model.dados_vendas(id_venda=codigo, data=datetime.now(), cliente_id=client_id,
                                           itens=self.carrinho, total=self.total_compra(),
                                           forma_pagamento=forma_pagamento, desconto=desconto)
            self.vendas_log.debug("Dados de venda recebidos")

            registra_venda = pd.DataFrame(self.vendas_model.vendas)
            arquivo_vazio = verificar_aquivo_vazio(self.vendas_data)
            registra_venda.to_csv(self.vendas_data, mode='a', encoding="utf-8", sep=",", header=arquivo_vazio,
                                  index=False)

            for item in self.carrinho:
                self.estoque.saida_estoque(item['produto_id'], item['quantidade'])

            self.vendas_model.vendas.clear()
            self.vendas_log.info(f"Venda: {codigo} registrada com sucesso")

            return "Compra finalizada"
        except Exception as e:
            self.vendas_log.exception(f"Erro ao finalizar venda: {e}")
            return f"Erro: {e}"
