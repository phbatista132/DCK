import pytest
import pandas as pd
from datetime import datetime, timedelta


class TestEstoqueControllerReposicao:
    """Testes de reposição de estoque"""

    def test_repor_estoque_sucesso(self, estoque_controller, produto_controller, produto_cadastrado):
        """Testa reposição com sucesso"""
        # Reposição
        resultado = estoque_controller.repor_estoque(produto_cadastrado, 5)

        assert "Item reposto" in resultado

        # Verificar estoque atualizado
        df = pd.read_csv(produto_controller.produtos_data)
        estoque_final = df[df['codigo'] == produto_cadastrado]['quantidade_estoque'].values[0]
        assert estoque_final == 15  # 10 inicial + 5

    def test_repor_quantidade_zero(self, estoque_controller, produto_cadastrado):
        """Testa rejeição de quantidade zero"""
        resultado = estoque_controller.repor_estoque(produto_cadastrado, 0)

        assert "zero" in resultado

    def test_repor_quantidade_negativa(self, estoque_controller, produto_cadastrado):
        """Testa rejeição de quantidade negativa"""
        resultado = estoque_controller.repor_estoque(produto_cadastrado, -5)

        assert "zero" in resultado

    def test_repor_produto_inexistente(self, estoque_controller):
        """Testa reposição de produto que não existe"""
        resultado = estoque_controller.repor_estoque(9999, 10)

        assert "não localizado" in resultado


class TestEstoqueControllerProdutoHabilitado:
    """Testes de verificação de produto habilitado"""

    def test_produto_ativo(self, estoque_controller, produto_cadastrado):
        """Testa produto ativo"""
        habilitado, msg = estoque_controller.produto_habilitado(produto_cadastrado)

        assert habilitado is True
        assert "Habilitado" in msg

    def test_produto_desabilitado(self, estoque_controller, produto_controller, produto_cadastrado):
        """Testa produto desabilitado"""
        # Desabilitar produto
        produto_controller.desabilitar_produto(produto_cadastrado)

        # Verificar
        habilitado, msg = estoque_controller.produto_habilitado(produto_cadastrado)

        assert habilitado is False
        assert "desabilitado" in msg

    def test_produto_inexistente(self, estoque_controller):
        """Testa produto que não existe"""
        habilitado, msg = estoque_controller.produto_habilitado(9999)

        assert habilitado is False
        assert "não localizado" in msg


class TestEstoqueControllerReservas:
    """Testes de sistema de reservas"""

    def test_reservar_com_estoque_disponivel(self, estoque_controller, produto_cadastrado):
        """Testa reserva com estoque disponível"""
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, 5)

        assert sucesso is True

        # Verificar reserva
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert info[produto_cadastrado]['quantidade'] == 5

    def test_reservar_estoque_completo(self, estoque_controller, produto_cadastrado):
        """Testa reservar exatamente todo o estoque"""
        # Produto tem 10 unidades
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, 10)

        # BUG CORRIGIDO: deve aceitar >= e não apenas >
        assert sucesso is True

    def test_reservar_mais_que_disponivel(self, estoque_controller, produto_cadastrado):
        """Testa reserva maior que estoque"""
        # Produto tem 10 unidades
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, 15)

        assert sucesso is False

    def test_reservar_quantidade_invalida(self, estoque_controller, produto_cadastrado):
        """Testa reserva com quantidade inválida"""
        # Quantidade zero
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, 0)
        assert sucesso is False

        # Quantidade negativa
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, -5)
        assert sucesso is False

    def test_multiplas_reservas_mesmo_produto(self, estoque_controller, produto_cadastrado):
        """Testa múltiplas reservas do mesmo produto"""
        # Primeira reserva
        estoque_controller.reservar_estoque(produto_cadastrado, 5)

        # Segunda reserva
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, 3)

        assert sucesso is True

        # Verificar total reservado
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert info[produto_cadastrado]['quantidade'] == 8  # 5 + 3

    def test_reserva_considera_reservas_existentes(self, estoque_controller, produto_cadastrado):
        """Testa que reserva considera outras reservas"""
        # Produto tem 10 unidades
        # Primeira reserva: 7 unidades (disponível: 3)
        estoque_controller.reservar_estoque(produto_cadastrado, 7)

        # Tentar reservar mais 5 (indisponível)
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, 5)
        assert sucesso is False

        # Tentar reservar 3 (exatamente o disponível)
        sucesso = estoque_controller.reservar_estoque(produto_cadastrado, 3)
        assert sucesso is True

    def test_liberar_reserva_parcial(self, estoque_controller, produto_cadastrado):
        """Testa liberação parcial de reserva"""
        # Reservar 10
        estoque_controller.reservar_estoque(produto_cadastrado, 10)

        # Liberar 5
        estoque_controller.liberar_reserva(produto_cadastrado, 5)

        # Verificar que restam 5
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert info[produto_cadastrado]['quantidade'] == 5

    def test_liberar_reserva_total(self, estoque_controller, produto_cadastrado):
        """Testa liberação total de reserva"""
        # Reservar 10
        estoque_controller.reservar_estoque(produto_cadastrado, 10)

        # Liberar todas (10)
        estoque_controller.liberar_reserva(produto_cadastrado, 10)

        # Verificar que reserva foi removida
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert produto_cadastrado not in info

    def test_liberar_sem_reservas(self, estoque_controller, produto_cadastrado):
        """Testa liberação sem reservas ativas"""
        resultado = estoque_controller.liberar_reserva(produto_cadastrado, 5)

        assert "Sem reservas" in resultado

    def test_reserva_com_expiracao(self, estoque_controller, produto_cadastrado):
        """Testa que reserva tem prazo de expiração"""
        # Reservar
        estoque_controller.reservar_estoque(produto_cadastrado, 5)

        # Verificar que tem prazo
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert 'expira_em' in info[produto_cadastrado]
        assert info[produto_cadastrado]['expira_em'] is not None

    @pytest.mark.slow
    def test_limpeza_reservas_expiradas(self, estoque_controller, produto_cadastrado):
        """Testa limpeza automática de reservas expiradas"""
        # Reservar com prazo curto (simular)
        estoque_controller.reservar_estoque(produto_cadastrado, 5)

        # Forçar expiração
        estoque_controller.reservas[produto_cadastrado]['expira_em'] = datetime.now() - timedelta(minutes=1)

        # Limpar reservas expiradas
        estoque_controller._limpar_reservas_expiradas()

        # Verificar que foi removida
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert produto_cadastrado not in info


class TestEstoqueControllerSaida:
    """Testes de saída de estoque"""

    def test_saida_com_estoque_suficiente(self, estoque_controller, produto_controller, produto_cadastrado):
        """Testa saída com estoque suficiente"""
        # Produto tem 10 unidades
        sucesso, msg = estoque_controller.saida_estoque(produto_cadastrado, 5)

        assert sucesso is True
        assert "realizada" in msg

        # Verificar estoque atualizado
        df = pd.read_csv(produto_controller.produtos_data)
        estoque_final = df[df['codigo'] == produto_cadastrado]['quantidade_estoque'].values[0]
        assert estoque_final == 5  # 10 - 5

    def test_saida_maior_que_estoque(self, estoque_controller, produto_controller, produto_cadastrado):
        """Testa rejeição de saída maior que estoque (BUG CRÍTICO)"""
        # Produto tem 10 unidades
        sucesso, msg = estoque_controller.saida_estoque(produto_cadastrado, 15)

        # BUG CORRIGIDO: deve rejeitar
        assert sucesso is False
        assert "insuficiente" in msg

        # Verificar que estoque não ficou negativo
        df = pd.read_csv(produto_controller.produtos_data)
        estoque = df[df['codigo'] == produto_cadastrado]['quantidade_estoque'].values[0]
        assert estoque >= 0

    def test_saida_libera_reserva_automaticamente(self, estoque_controller, produto_cadastrado):
        """Testa que saída libera reserva automaticamente"""
        # Reservar 10
        estoque_controller.reservar_estoque(produto_cadastrado, 10)

        # Verificar reserva
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert info[produto_cadastrado]['quantidade'] == 10

        # Fazer saída de 10
        estoque_controller.saida_estoque(produto_cadastrado, 10)

        # Verificar que reserva foi liberada
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert produto_cadastrado not in info

    def test_saida_produto_inexistente(self, estoque_controller):
        """Testa saída de produto que não existe"""
        sucesso, msg = estoque_controller.saida_estoque(9999, 5)

        assert sucesso is False
        assert "não encontrado" in msg


class TestEstoqueControllerIntegracao:
    """Testes de integração do EstoqueController"""

    def test_fluxo_completo_estoque(self, estoque_controller, produto_controller, produto_cadastrado):
        """Testa fluxo completo: reserva → saída → reposição"""
        # 1. Estoque inicial: 10
        df = pd.read_csv(produto_controller.produtos_data)
        estoque_inicial = df[df['codigo'] == produto_cadastrado]['quantidade_estoque'].values[0]
        assert estoque_inicial == 10

        # 2. Reservar 5
        estoque_controller.reservar_estoque(produto_cadastrado, 5)
        info = estoque_controller.obter_info_reservas(produto_cadastrado)
        assert info[produto_cadastrado]['quantidade'] == 5

        # 3. Saída de 5 (libera reserva)
        sucesso, _ = estoque_controller.saida_estoque(produto_cadastrado, 5)
        assert sucesso is True

        # 4. Estoque após saída: 5
        df = pd.read_csv(produto_controller.produtos_data)
        estoque_apos_saida = df[df['codigo'] == produto_cadastrado]['quantidade_estoque'].values[0]
        assert estoque_apos_saida == 5

        # 5. Reposição de 10
        estoque_controller.repor_estoque(produto_cadastrado, 10)

        # 6. Estoque final: 15
        df = pd.read_csv(produto_controller.produtos_data)
        estoque_final = df[df['codigo'] == produto_cadastrado]['quantidade_estoque'].values[0]
        assert estoque_final == 15