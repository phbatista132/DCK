import pytest
from datetime import datetime
from src.models.vendas import Venda, ItemVenda


class TestItemVendaModel:
    """Testes unitários do Model ItemVenda"""

    # ==================== TESTES DE CRIAÇÃO ====================

    def test_criar_item_venda_valido(self):
        """Testa criação de item de venda válido"""
        item = ItemVenda(
            produto_id=1,
            nome_produto="Notebook Dell",
            quantidade=2,
            preco_unitario=3500.0,
            subtotal=7000.0
        )

        assert item.produto_id == 1
        assert item.nome_produto

        assert item.nome_produto == "Notebook Dell"
        assert item.quantidade == 2
        assert item.preco_unitario == 3500.0
        assert item.subtotal == 7000.0

    def test_recalcular_subtotal_automaticamente(self):
        """Testa recálculo automático do subtotal"""
        item = ItemVenda(
            produto_id=1,
            nome_produto="Mouse",
            quantidade=3,
            preco_unitario=50.0,
            subtotal=0.0  # Será recalculado
        )

        # Subtotal deve ser recalculado para 150.0
        assert item.subtotal == 150.0

    def test_subtotal_com_valores_decimais(self):
        """Testa subtotal com valores decimais"""
        item = ItemVenda(
            produto_id=1,
            nome_produto="Teclado",
            quantidade=2,
            preco_unitario=125.50,
            subtotal=0.0
        )

        assert item.subtotal == pytest.approx(251.0, rel=0.01)

        # ==================== TESTES DE VALIDAÇÃO ====================

    def test_rejeitar_quantidade_zero(self):
        """Testa rejeição de quantidade zero"""
        with pytest.raises(ValueError, match="Quantidade deve ser positiva"):
            ItemVenda(
                produto_id=1,
                nome_produto="Teste",
                quantidade=0,
                preco_unitario=100.0,
                subtotal=0.0
            )

    def test_rejeitar_quantidade_negativa(self):
        """Testa rejeição de quantidade negativa"""
        with pytest.raises(ValueError, match="Quantidade deve ser positiva"):
            ItemVenda(
                produto_id=1,
                nome_produto="Teste",
                quantidade=-5,
                preco_unitario=100.0,
                subtotal=0.0
            )

    def test_rejeitar_preco_negativo(self):
        """Testa rejeição de preço negativo"""
        with pytest.raises(ValueError, match="Preço unitário não pode ser negativo"):
            ItemVenda(
                produto_id=1,
                nome_produto="Teste",
                quantidade=1,
                preco_unitario=-100.0,
                subtotal=0.0
            )

        # ==================== TESTES DE MEMÓRIA ====================

    @pytest.mark.memory
    def test_tamanho_item_venda(self):
        """Testa tamanho de um ItemVenda em memória"""
        from pympler import asizeof

        item = ItemVenda(
            produto_id=1,
            nome_produto="Notebook Dell Inspiron 15",
            quantidade=1,
            preco_unitario=3500.0,
            subtotal=3500.0
        )

        tamanho = asizeof.asizeof(item)
        tamanho_kb = tamanho / 1024

        print(f"\n🔍 Tamanho ItemVenda: {tamanho} bytes ({tamanho_kb:.2f} KB)")

        # ItemVenda deve ocupar menos de 0.5 KB
        assert tamanho < 512, f"ItemVenda muito grande: {tamanho} bytes"


class TestVendaModel:
    """Testes unitários do Model Venda"""

    # ==================== FIXTURES ====================

    @pytest.fixture
    def itens_venda_validos(self):
        """Fixture com itens de venda válidos"""
        return [
            ItemVenda(
                produto_id=1,
                nome_produto="Notebook",
                quantidade=1,
                preco_unitario=3000.0,
                subtotal=3000.0
            ),
            ItemVenda(
                produto_id=2,
                nome_produto="Mouse",
                quantidade=2,
                preco_unitario=50.0,
                subtotal=100.0
            ),
            ItemVenda(
                produto_id=3,
                nome_produto="Teclado",
                quantidade=1,
                preco_unitario=200.0,
                subtotal=200.0
            )
        ]

    # ==================== TESTES DE CRIAÇÃO ====================

    def test_criar_venda_valida(self, itens_venda_validos, datetime_valida):
        """Testa criação de venda com dados válidos"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime_valida,
            itens=itens_venda_validos,
            subtotal=0.0,  # Será calculado
            desconto=0.0,
            total=0.0,  # Será calculado
            forma_pagamento="Cartão",
            status="finalizada",
            cliente_id=1
        )

        assert venda.id_venda == 1
        assert venda.data_hora == datetime_valida
        assert len(venda.itens) == 3
        assert venda.subtotal == 3300.0  # Calculado automaticamente
        assert venda.desconto == 0.0
        assert venda.total == 3300.0
        assert venda.forma_pagamento == "Cartão"
        assert venda.status == "finalizada"
        assert venda.cliente_id == 1
        assert venda.data_finalizacao is not None

    def test_calcular_subtotal_automaticamente(self, itens_venda_validos):
        """Testa cálculo automático do subtotal"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        # 3000 + 100 + 200 = 3300
        assert venda.subtotal == 3300.0

    def test_calcular_total_sem_desconto(self, itens_venda_validos):
        """Testa cálculo do total sem desconto"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        assert venda.total == venda.subtotal

    def test_venda_sem_cliente(self, itens_venda_validos):
        """Testa criação de venda sem cliente (opcional)"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro",
            cliente_id=None
        )

        assert venda.cliente_id is None
        assert not venda.tem_cliente()

    def test_data_finalizacao_automatica(self, itens_venda_validos):
        """Testa criação automática de data_finalizacao"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="PIX"
        )

        assert venda.data_finalizacao is not None
        assert isinstance(venda.data_finalizacao, datetime)

    # ==================== TESTES DE VALIDAÇÃO ====================

    def test_rejeitar_venda_sem_itens(self):
        """Testa rejeição de venda sem itens"""
        with pytest.raises(ValueError, match="Venda deve ter pelo menos um item"):
            Venda(
                id_venda=1,
                data_hora=datetime.now(),
                itens=[],  # Lista vazia
                subtotal=0.0,
                desconto=0.0,
                total=0.0,
                forma_pagamento="Dinheiro"
            )

    # ==================== TESTES DE DESCONTO ====================

    def test_aplicar_desconto_percentual(self, itens_venda_validos):
        """Testa aplicação de desconto percentual"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        # Subtotal = 3300
        valor_desconto = venda.aplicar_desconto(10)  # 10%

        assert valor_desconto == 330.0
        assert venda.desconto == 330.0
        assert venda.total == 2970.0  # 3300 - 330

    def test_aplicar_desconto_pequeno(self, itens_venda_validos):
        """Testa desconto pequeno (1%)"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        valor_desconto = venda.aplicar_desconto(1)

        assert valor_desconto == 33.0
        assert venda.desconto == 33.0
        assert venda.total == 3267.0

    def test_aplicar_desconto_total(self, itens_venda_validos):
        """Testa desconto de 100%"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Cortesia"
        )

        valor_desconto = venda.aplicar_desconto(100)

        assert valor_desconto == 3300.0
        assert venda.desconto == 3300.0
        assert venda.total == 0.0

    def test_rejeitar_desconto_negativo(self, itens_venda_validos):
        """Testa rejeição de desconto negativo"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        with pytest.raises(ValueError, match="Desconto deve estar entre 0 e 100"):
            venda.aplicar_desconto(-10)

    def test_rejeitar_desconto_maior_100(self, itens_venda_validos):
        """Testa rejeição de desconto > 100%"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        with pytest.raises(ValueError, match="Desconto deve estar entre 0 e 100"):
            venda.aplicar_desconto(150)

    def test_aplicar_multiplos_descontos(self, itens_venda_validos):
        """Testa aplicação de múltiplos descontos (sobrescreve)"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        venda.aplicar_desconto(10)  # 330
        assert venda.desconto == 330.0

        venda.aplicar_desconto(20)  # 660 (sobrescreve)
        assert venda.desconto == 660.0
        assert venda.total == 2640.0

    # ==================== TESTES DE MÉTODOS ====================

    def test_tem_cliente_verdadeiro(self, itens_venda_validos):
        """Testa verificação de cliente (True)"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro",
            cliente_id=1
        )

        assert venda.tem_cliente() is True

    def test_tem_cliente_falso(self, itens_venda_validos):
        """Testa verificação de cliente (False)"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro",
            cliente_id=None
        )

        assert venda.tem_cliente() is False

    # ==================== TESTES DE CONVERSÃO ====================

    def test_to_dict(self, itens_venda_validos):
        """Testa conversão para dicionário"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime(2025, 1, 15, 14, 30, 0),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Cartão",
            cliente_id=5
        )
        venda.aplicar_desconto(3.04)
        dict_venda = venda.to_dict()


        assert isinstance(dict_venda, dict)
        assert dict_venda['id_venda'] == 1
        assert dict_venda['data'] == "2025-01-15T14:30:00"
        assert dict_venda['cliente_id'] == 5
        assert dict_venda['subtotal'] == 3300.0
        assert dict_venda['desconto'] == 100.32
        assert dict_venda['total'] == 3199.68
        assert dict_venda['forma_pagamento'] == "Cartão"
        assert dict_venda['status'] == "finalizada"
        assert 'data_finalizacao' in dict_venda

    def test_itens_to_list(self, itens_venda_validos):
        """Testa conversão de itens para lista"""
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        lista_itens = venda.itens_to_list()

        assert isinstance(lista_itens, list)
        assert len(lista_itens) == 3

        # Verificar primeiro item
        item = lista_itens[0]
        assert item['id_item'] == "1_1"
        assert item['id_venda'] == 1
        assert item['produto_id'] == 1
        assert item['nome_produto'] == "Notebook"
        assert item['quantidade'] == 1
        assert item['preco_unitario'] == 3000.0
        assert item['subtotal'] == 3000.0

    # ==================== TESTES DE MEMÓRIA ====================

    @pytest.mark.memory
    def test_tamanho_venda(self, itens_venda_validos):
        """Testa tamanho de uma Venda em memória"""
        from pympler import asizeof

        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens_venda_validos,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Cartão de Crédito Parcelado",
            cliente_id=1
        )

        tamanho = asizeof.asizeof(venda)
        tamanho_kb = tamanho / 1024

        print(f"\n🔍 Tamanho Venda (3 itens): {tamanho} bytes ({tamanho_kb:.2f} KB)")

        # Venda com 3 itens deve ocupar menos de 2 KB
        assert tamanho < 2048, f"Venda muito grande: {tamanho} bytes"


class TestVendaIntegration:
    """Testes de integração de Venda"""

    def test_venda_com_muitos_itens(self):
        """Testa venda com muitos itens"""
        itens = [
            ItemVenda(
                produto_id=i,
                nome_produto=f"Produto {i}",
                quantidade=1,
                preco_unitario=100.0,
                subtotal=100.0
            )
            for i in range(50)
        ]

        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Dinheiro"
        )

        assert len(venda.itens) == 50
        assert venda.subtotal == 5000.0
        assert venda.total == 5000.0

    def test_calcular_total_complexo(self):
        """Testa cálculo com valores decimais complexos"""
        itens = [
            ItemVenda(
                produto_id=1,
                nome_produto="Item 1",
                quantidade=3,
                preco_unitario=123.45,
                subtotal=0.0
            ),
            ItemVenda(
                produto_id=2,
                nome_produto="Item 2",
                quantidade=5,
                preco_unitario=67.89,
                subtotal=0.0
            ),
            ItemVenda(
                produto_id=3,
                nome_produto="Item 3",
                quantidade=2,
                preco_unitario=456.78,
                subtotal=0.0
            )
        ]

        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="PIX"
        )

        # (3 * 123.45) + (5 * 67.89) + (2 * 456.78)
        # = 370.35 + 339.45 + 913.56 = 1623.36
        assert venda.subtotal == pytest.approx(1623.36, rel=0.01)

        # Aplicar desconto de 15%
        venda.aplicar_desconto(15)
        assert venda.desconto == pytest.approx(243.50, rel=0.01)
        assert venda.total == pytest.approx(1379.86, rel=0.01)

    @pytest.mark.memory
    def test_memoria_100_vendas(self):
        """Testa consumo de memória com 100 vendas"""
        from pympler import asizeof

        vendas = []
        for i in range(100):
            itens = [
                ItemVenda(
                    produto_id=j,
                    nome_produto=f"Produto {j}",
                    quantidade=1,
                    preco_unitario=100.0,
                    subtotal=100.0
                )
                for j in range(3)  # 3 itens por venda
            ]

            venda = Venda(
                id_venda=i,
                data_hora=datetime.now(),
                itens=itens,
                subtotal=0.0,
                desconto=0.0,
                total=0.0,
                forma_pagamento="Dinheiro"
            )
            vendas.append(venda)

        tamanho_total = asizeof.asizeof(vendas)
        tamanho_mb = tamanho_total / (1024 * 1024)

        print(f"\n🔍 100 Vendas (3 itens cada): {tamanho_mb:.2f} MB")

        # 100 vendas devem ocupar menos de 1 MB
        assert tamanho_mb < 1.0, f"100 vendas ocupam {tamanho_mb:.2f} MB"

    def test_fluxo_completo_venda(self):
        """Testa fluxo completo de uma venda"""
        # 1. Criar itens
        itens = [
            ItemVenda(
                produto_id=1,
                nome_produto="Notebook",
                quantidade=1,
                preco_unitario=3000.0,
                subtotal=3000.0
            ),
            ItemVenda(
                produto_id=2,
                nome_produto="Mouse",
                quantidade=2,
                preco_unitario=50.0,
                subtotal=100.0
            )
        ]

        # 2. Criar venda
        venda = Venda(
            id_venda=1,
            data_hora=datetime.now(),
            itens=itens,
            subtotal=0.0,
            desconto=0.0,
            total=0.0,
            forma_pagamento="Cartão",
            cliente_id=1
        )

        # 3. Verificar cálculos iniciais
        assert venda.subtotal == 3100.0
        assert venda.total == 3100.0
        assert venda.tem_cliente()

        # 4. Aplicar desconto
        venda.aplicar_desconto(10)
        assert venda.desconto == 310.0
        assert venda.total == 2790.0

        # 5. Converter para dict
        dict_venda = venda.to_dict()
        assert dict_venda['total'] == 2790.0

        # 6. Converter itens para lista
        lista_itens = venda.itens_to_list()
        assert len(lista_itens) == 2

        print("\n✅ Fluxo completo de venda executado com sucesso!")