import pytest
from datetime import date
from src.models.produto import Produto


class TestProdutoModel:
    """Testes do model produto"""

    def test_criar_produto_valido(self):
        """Testa criação de produto com dados validos"""

        produto = Produto(
            codigo=1,
            nome='Notebook Dell',
            modelo="Inspirion 15",
            categoria="Eletrônicos",
            valor=3500.0,
            quantidade_estoque=10,
            vlr_compra=2800.0,
            margem_lucro=0,
            dt_cadastro=date.today(),
        )

        assert produto.codigo == 1
        assert produto.nome == "Notebook Dell"
        assert produto.modelo == "Inspirion 15"
        assert produto.categoria == "Eletrônicos"
        assert produto.valor == 3500.0
        assert produto.quantidade_estoque == 10
        assert produto.vlr_compra == 2800.0
        assert produto.margem_lucro == pytest.approx(25.0, rel=0.01)
        assert produto.ativo is True

    def test_criar_produto_com_valores_minimos(self):
        """Testa criação com valores mínimos válidos"""
        produto = Produto(
            codigo=1,
            nome="A",
            modelo="B",
            categoria="C",
            valor=0.01,
            quantidade_estoque=0,
            vlr_compra=0.01,
            margem_lucro=0,
            dt_cadastro=date.today()
        )

        assert produto.valor == 0.01
        assert produto.quantidade_estoque == 0

    def test_produto_calcula_margem_corretamente(self):
        """Testa calculo de margem de lucro"""
        produto = Produto(
            codigo=1,
            nome='Mouse',
            modelo="Logitech",
            categoria="Periféricos",
            valor=100.0,
            quantidade_estoque=50,
            vlr_compra=50.0,
            margem_lucro=0,
            dt_cadastro=date.today(),
        )

        assert produto.margem_lucro == 100.0

    def test_margem_lucro_com_valores_decimais(self):
        """Testa margem com valores decimais"""
        produto = Produto(
            codigo=1,
            nome="Produto Teste",
            modelo="Test",
            categoria="Test",
            valor=157.89,
            quantidade_estoque=10,
            vlr_compra=123.45,
            margem_lucro=0,
            dt_cadastro=date.today()
        )

        # (157.89 - 123.45) / 123.45 * 100 = 27.89%
        assert produto.margem_lucro == pytest.approx(27.89, rel=0.01)

    def test_produto_rejeita_valor_negativo(self):
        """Testa validação de valor negativo"""

        with pytest.raises(ValueError, match="Valor deve ser positivo"):
            Produto(
                codigo=1,
                nome="Teste",
                modelo="Test",
                categoria="Test",
                valor=-100.0,
                quantidade_estoque=50,
                vlr_compra=50.0,
                margem_lucro=0,
                dt_cadastro=date.today(),
            )

    def test_rejeitar_vlr_compra_negativo(self):
        """Testa rejeição de valor de compra negativo"""
        with pytest.raises(ValueError, match="Valor de compra deve ser positivo"):
            Produto(
                codigo=1,
                nome="Teste",
                modelo="Test",
                categoria="Test",
                valor=100.0,
                quantidade_estoque=10,
                vlr_compra=-50.0,
                margem_lucro=0,
                dt_cadastro=date.today()
            )

    def test_rejeitar_quantidade_negativa(self):
        """Testa rejeição de quantidade negativa"""
        with pytest.raises(ValueError, match="Quantidade estoque deve ser positivo"):
            Produto(
                codigo=1,
                nome="Teste",
                modelo="Test",
                categoria="Test",
                valor=100.0,
                quantidade_estoque=-10,
                vlr_compra=50.0,
                margem_lucro=0,
                dt_cadastro=date.today()
            )

    def test_produto_to_dict(self):
        """Testa conversão para dicionario"""
        produto = Produto(
            codigo=1,
            nome="Teclado",
            modelo="Mecânico",
            categoria="Perifericos",
            valor=200.0,
            quantidade_estoque=50,
            vlr_compra=150.0,
            margem_lucro=0,
            dt_cadastro=date(2025, 1, 1),
        )

        dict_produto = produto.to_dict()

        assert dict_produto["codigo"] == 1
        assert dict_produto["nome"] == "Teclado"
        assert dict_produto["data_cadastro"] == "2025-01-01"

    def test_str_formatacao(self):
        """Testa formatação string do produto"""
        produto = Produto(
            codigo=1,
            nome="Mouse Gamer",
            modelo="Razer",
            categoria="Periféricos",
            valor=250.0,
            quantidade_estoque=15,
            vlr_compra=180.0,
            margem_lucro=0,
            dt_cadastro=date.today()
            )

        str_produto = str(produto)

        assert "Mouse Gamer" in str_produto
        assert "Razer" in str_produto
        assert "Periféricos" in str_produto
        assert "250" in str_produto
        assert "15" in str_produto

        # ==================== TESTES DE MEMÓRIA ====================

        @pytest.mark.memory
        def test_tamanho_objeto_produto():
            """Testa tamanho do objeto Produto em memória"""
            from pympler import asizeof

            produto = Produto(
                codigo=1,
                nome="Notebook Dell Inspiron 15 3000",
                modelo="Inspiron 15 3000 Series",
                categoria="Eletrônicos e Informática",
                valor=3500.0,
                quantidade_estoque=10,
                vlr_compra=2800.0,
                margem_lucro=25.0,
                dt_cadastro=date.today()
            )

            tamanho = asizeof.asizeof(produto)
            tamanho_kb = tamanho / 1024

            print(f"\n🔍 Tamanho Produto: {tamanho} bytes ({tamanho_kb:.2f} KB)")

            # Produto deve ocupar menos de 1 KB
            assert tamanho < 1024, f"Produto muito grande: {tamanho} bytes"

    class TestProdutoIntegration:
        """Testes de integração do Produto"""

        def test_criar_multiplos_produtos(self):
            """Testa criação de múltiplos produtos"""
            produtos = []

            for i in range(100):
                produto = Produto(
                    codigo=i,
                    nome=f"Produto {i}",
                    modelo=f"Modelo {i}",
                    categoria="Categoria Teste",
                    valor=100.0 + i,
                    quantidade_estoque=10,
                    vlr_compra=80.0 + i,
                    margem_lucro=0,
                    dt_cadastro=date.today()
                )
                produtos.append(produto)

            assert len(produtos) == 100
            assert all(p.esta_ativo() for p in produtos)

        @pytest.mark.memory
        def test_memoria_100_produtos(self):
            """Testa consumo de memória com 100 produtos"""
            from pympler import asizeof

            produtos = [
                Produto(
                    codigo=i,
                    nome=f"Produto {i}",
                    modelo=f"Modelo {i}",
                    categoria="Test",
                    valor=100.0,
                    quantidade_estoque=10,
                    vlr_compra=80.0,
                    margem_lucro=0,
                    dt_cadastro=date.today()
                )
                for i in range(100)
            ]

            tamanho_total = asizeof.asizeof(produtos)
            tamanho_mb = tamanho_total / (1024 * 1024)

            print(f"\n🔍 100 Produtos: {tamanho_mb:.2f} MB")

            # 100 produtos devem ocupar menos de 0.5 MB
            assert tamanho_mb < 0.5, f"100 produtos ocupam {tamanho_mb:.2f} MB"