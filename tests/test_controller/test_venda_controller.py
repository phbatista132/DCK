# tests/test_controllers/test_venda_controller.py
"""
Testes do VendaController
"""
import pytest
import pandas as pd


class TestVendaControllerCarrinho:
    """Testes de gerenciamento de carrinho"""

    def test_adicionar_item_sucesso(self, venda_controller, produto_controller):
        """Testa adição de item ao carrinho"""
        # Cadastrar produto
        produto_controller.cadastrar_produto(
            "Mouse", "Logitech", "Periféricos", 80.0, 20, 50.0
        )

        # Adicionar ao carrinho
        resultado = venda_controller.adicionar_item(1, 2)

        assert "adicionado" in resultado
        assert len(venda_controller.carrinho) == 1
        assert venda_controller.carrinho[0]['quantidade'] == 2
        assert venda_controller.carrinho[0]['subtotal'] == 160.0

    def test_adicionar_produto_inexistente(self, venda_controller):
        """Testa adição de produto que não existe"""
        resultado = venda_controller.adicionar_item(9999, 1)

        assert "não encontrado" in resultado

    def test_adicionar_produto_desabilitado(self, venda_controller, produto_controller):
        """Testa adição de produto desabilitado"""
        # Cadastrar e desabilitar
        produto_controller.cadastrar_produto(
            "Produto", "Modelo", "Cat", 100.0, 10, 80.0
        )
        produto_controller.desabilitar_produto(1)

        # Tentar adicionar
        resultado = venda_controller.adicionar_item(1, 1)

        assert "desabilitado" in resultado

    def test_adicionar_quantidade_indisponivel(self, venda_controller, produto_controller):
        """Testa adição de quantidade maior que estoque"""
        # Cadastrar produto com estoque 5
        produto_controller.cadastrar_produto(
            "Produto", "Modelo", "Cat", 100.0, 5, 80.0
        )

        # Tentar adicionar 10 (indisponível)
        resultado = venda_controller.adicionar_item(1, 10)

        assert "indisponivel" in resultado

    def test_adicionar_reserva_estoque(self, venda_controller, produto_controller):
        """Testa que adicionar item reserva estoque"""
        # Cadastrar produto com estoque 10
        produto_controller.cadastrar_produto(
            "Produto", "Modelo", "Cat", 100.0, 10, 80.0
        )

        # Adicionar 5 ao carrinho
        venda_controller.adicionar_item(1, 5)

        # Verificar reserva
        info = venda_controller.estoque.obter_info_reservas(1)
        assert info[1]['quantidade'] == 5

    def test_ver_carrinho(self, venda_controller, produto_controller):
        """Testa visualização do carrinho"""
        # Adicionar itens
        produto_controller.cadastrar_produto("P1", "M1", "C1", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("P2", "M2", "C2", 200.0, 10, 150.0)

        venda_controller.adicionar_item(1, 2)
        venda_controller.adicionar_item(2, 1)

        # Ver carrinho
        carrinho = venda_controller.ver_carinho()

        assert len(carrinho) == 2
        assert carrinho[0]['produto_id'] == 1
        assert carrinho[1]['produto_id'] == 2

    def test_remover_item_sucesso(self, venda_controller, produto_controller):
        """Testa remoção de item do carrinho"""
        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 5)

        # Remover
        resultado = venda_controller.remover_item(1)

        assert "removido" in resultado
        assert len(venda_controller.carrinho) == 0

    def test_remover_item_libera_reserva(self, venda_controller, produto_controller):
        """Testa que remover item libera reserva"""
        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 5)

        # Verificar reserva
        info = venda_controller.estoque.obter_info_reservas(1)
        assert 1 in info

        # Remover
        venda_controller.remover_item(1)

        # Verificar que reserva foi liberada
        info = venda_controller.estoque.obter_info_reservas(1)
        assert 1 not in info

    def test_remover_item_inexistente(self, venda_controller):
        """Testa remoção de item que não está no carrinho"""
        resultado = venda_controller.remover_item(9999)

        assert "não encotrado" in resultado or "não encontrado" in resultado

    def test_alterar_quantidade_aumentar(self, venda_controller, produto_controller):
        """Testa aumento de quantidade"""
        # Adicionar item com quantidade 2
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 2)

        # Aumentar para 5
        resultado = venda_controller.alterar_quantidade(1, 5)

        assert "sucesso" in resultado
        assert venda_controller.carrinho[0]['quantidade'] == 5
        assert venda_controller.carrinho[0]['subtotal'] == 500.0

    def test_alterar_quantidade_diminuir(self, venda_controller, produto_controller):
        """Testa diminuição de quantidade"""
        # Adicionar item com quantidade 5
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 5)

        # Diminuir para 2
        resultado = venda_controller.alterar_quantidade(1, 2)

        assert "sucesso" in resultado
        assert venda_controller.carrinho[0]['quantidade'] == 2
        assert venda_controller.carrinho[0]['subtotal'] == 200.0

    def test_alterar_quantidade_zero(self, venda_controller, produto_controller):
        """Testa rejeição de quantidade zero"""
        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 2)

        # Tentar alterar para zero
        resultado = venda_controller.alterar_quantidade(1, 0)

        assert "maior que zero" in resultado

    def test_alterar_quantidade_indisponivel(self, venda_controller, produto_controller):
        """Testa alteração para quantidade indisponível"""
        # Produto com estoque 10
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 5)

        # Tentar alterar para 15 (mais que estoque)
        resultado = venda_controller.alterar_quantidade(1, 15)

        assert "insuficiente" in resultado

    def test_alterar_quantidade_item_inexistente(self, venda_controller):
        """Testa alteração de item que não está no carrinho"""
        resultado = venda_controller.alterar_quantidade(9999, 5)

        assert "não encontrado" in resultado


class TestVendaControllerFinalizacao:
    """Testes de finalização de venda"""

    def test_finalizar_venda_sem_cliente(self, venda_controller, produto_controller):
        """Testa finalização sem cliente (opcional)"""
        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 2)

        # Finalizar sem cliente
        resultado = venda_controller.finalizar_venda()

        assert "finalizada" in resultado
        assert "ID:" in resultado
        assert len(venda_controller.carrinho) == 0

    def test_finalizar_venda_com_cliente(self, venda_controller, produto_controller):
        """Testa finalização com cliente"""
        # Cadastrar cliente
        venda_controller.cliente.cadastrar_cliente(
            "João Silva", "15/05/1990", "49209207840", "Rua", "(11) 99999-9999"
        )

        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 2)

        # Finalizar com cliente
        resultado = venda_controller.finalizar_venda(cpf_cliente="49209207840")

        assert "finalizada" in resultado

        # Verificar que venda foi salva com cliente_id
        df = pd.read_csv(venda_controller.vendas_data)
        cliente_id = df.iloc[0]['cliente_id']
        assert pd.notna(cliente_id)

    def test_finalizar_venda_cliente_inexistente(self, venda_controller, produto_controller):
        """Testa finalização com cliente inexistente"""
        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 1)

        # Tentar finalizar com CPF inexistente
        resultado = venda_controller.finalizar_venda(cpf_cliente="00000000000")

        assert "não encontrado" in resultado

    def test_finalizar_venda_cliente_inativo(self, venda_controller, produto_controller):
        """Testa finalização com cliente inativo"""
        # Cadastrar e desativar cliente
        venda_controller.cliente.cadastrar_cliente(
            "João", "15/05/1990", "49209207840", "Rua", "(11) 99999-9999"
        )
        venda_controller.cliente.desativar_cliente("49209207840")

        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 1)

        # Tentar finalizar com cliente inativo
        resultado = venda_controller.finalizar_venda(cpf_cliente="49209207840")

        assert "inativo" in resultado

    def test_finalizar_venda_carrinho_vazio(self, venda_controller):
        """Testa finalização com carrinho vazio"""
        resultado = venda_controller.finalizar_venda()

        assert "vazio" in resultado

    def test_finalizar_venda_com_desconto(self, venda_controller, produto_controller):
        """Testa finalização com desconto"""
        # Adicionar item (subtotal 200)
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 2)

        # Finalizar com 10% desconto
        resultado = venda_controller.finalizar_venda(percentual_desconto=10)

        assert "finalizada" in resultado

        # Verificar desconto aplicado
        df = pd.read_csv(venda_controller.vendas_data)
        desconto = float(df.iloc[0]['desconto'])
        total = float(df.iloc[0]['total'])

        assert desconto == 20.0  # 10% de 200
        assert total == 180.0  # 200 - 20

    def test_finalizar_venda_desconto_invalido(self, venda_controller, produto_controller):
        """Testa finalização com desconto inválido"""
        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 1)

        # Tentar finalizar com desconto > 100%
        resultado = venda_controller.finalizar_venda(percentual_desconto=150)

        assert "Erro" in resultado

    def test_finalizar_venda_da_baixa_estoque(self, venda_controller, produto_controller):
        """Testa que finalizar venda dá baixa no estoque"""
        # Produto com estoque 10
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)

        # Adicionar 5 ao carrinho
        venda_controller.adicionar_item(1, 5)

        # Finalizar
        venda_controller.finalizar_venda()

        # Verificar estoque após venda
        df = pd.read_csv(produto_controller.produtos_data)
        estoque_final = df.iloc[0]['quantidade_estoque']

        assert estoque_final == 5  # 10 - 5

    def test_finalizar_venda_limpa_carrinho(self, venda_controller, produto_controller):
        """Testa que finalizar limpa o carrinho"""
        # Adicionar itens
        produto_controller.cadastrar_produto("P1", "M", "C", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("P2", "M", "C", 200.0, 10, 150.0)
        venda_controller.adicionar_item(1, 1)
        venda_controller.adicionar_item(2, 1)

        # Finalizar
        venda_controller.finalizar_venda()

        # Verificar carrinho vazio
        assert len(venda_controller.carrinho) == 0

    def test_finalizar_venda_libera_reservas(self, venda_controller, produto_controller):
        """Testa que finalizar libera todas as reservas"""
        # Adicionar item
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 5)

        # Verificar reserva
        info = venda_controller.estoque.obter_info_reservas(1)
        assert 1 in info

        # Finalizar
        venda_controller.finalizar_venda()

        # Verificar que reserva foi liberada
        info = venda_controller.estoque.obter_info_reservas(1)
        assert 1 not in info

    def test_gerar_id_venda_sequencial(self, venda_controller, produto_controller):
        """Testa geração sequencial de IDs de venda"""
        # Cadastrar produto
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)

        # Primeira venda
        venda_controller.adicionar_item(1, 1)
        venda_controller.finalizar_venda()

        # Segunda venda
        venda_controller.adicionar_item(1, 1)
        venda_controller.finalizar_venda()

        # Verificar IDs sequenciais
        df = pd.read_csv(venda_controller.vendas_data)
        assert df.iloc[0]['id_venda'] == 1
        assert df.iloc[1]['id_venda'] == 2


class TestVendaControllerCancelamento:
    """Testes de cancelamento de venda"""

    def test_cancelar_venda_sucesso(self, venda_controller, produto_controller):
        """Testa cancelamento de venda"""
        # Adicionar itens
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 5)

        # Cancelar
        resultado = venda_controller.cancelar_venda()

        assert "sucesso" in resultado
        assert len(venda_controller.carrinho) == 0

    def test_cancelar_venda_libera_reservas(self, venda_controller, produto_controller):
        """Testa que cancelar libera todas as reservas"""
        # Adicionar itens
        produto_controller.cadastrar_produto("Produto", "M", "C", 100.0, 10, 80.0)
        venda_controller.adicionar_item(1, 5)

        # Verificar reserva
        info = venda_controller.estoque.obter_info_reservas(1)
        assert 1 in info

        # Cancelar
        venda_controller.cancelar_venda()

        # Verificar que reserva foi liberada
        info = venda_controller.estoque.obter_info_reservas(1)
        assert 1 not in info

    def test_cancelar_carrinho_vazio(self, venda_controller):
        """Testa cancelamento com carrinho vazio"""
        resultado = venda_controller.cancelar_venda()

        assert "vazio" in resultado


class TestVendaControllerIntegracao:
    """Testes de integração do VendaController"""

    def test_fluxo_completo_venda(self, venda_controller, produto_controller):
        """Testa fluxo completo de venda"""
        # 1. Cadastrar produtos
        produto_controller.cadastrar_produto("Notebook", "Dell", "Eletrônicos", 3000.0, 5, 2500.0)
        produto_controller.cadastrar_produto("Mouse", "Logitech", "Periféricos", 80.0, 20, 50.0)

        # 2. Adicionar ao carrinho
        venda_controller.adicionar_item(1, 1)  # Notebook
        venda_controller.adicionar_item(2, 2)  # 2 Mouses

        # 3. Verificar carrinho
        carrinho = venda_controller.ver_carinho()
        assert len(carrinho) == 2

        # 4. Alterar quantidade
        venda_controller.alterar_quantidade(2, 3)  # 3 mouses

        # 5. Calcular subtotal
        subtotal = venda_controller._calcular_subtotal()
        assert subtotal == 3240.0  # 3000 + (80*3)

        # 6. Finalizar com desconto
        resultado = venda_controller.finalizar_venda(percentual_desconto=10)
        assert "finalizada" in resultado

        # 7. Verificar venda salva
        df = pd.read_csv(venda_controller.vendas_data)
        assert len(df) == 1
        assert df.iloc[0]['desconto'] == 324.0  # 10% de 3240
        assert df.iloc[0]['total'] == 2916.0  # 3240 - 324