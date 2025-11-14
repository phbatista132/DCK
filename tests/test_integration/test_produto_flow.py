class TestProdutoFlow:
    """Testes de fluxo de produtos"""

    def test_cadastro_e_busca_produto(self, db_session, produto_controller):
        """Testa cadastro e busca de produto"""
        # 1. Cadastrar
        resultado = produto_controller.cadastrar_produto(
            db=db_session,
            nome="Mouse Logitech",
            modelo="MX Master 3",
            categoria="Periféricos",
            valor=450.00,
            quantidade_estoque=50,
            vlr_compra=300.00
        )

        assert "sucesso" in resultado

        # 2. Buscar
        resultado_busca = produto_controller.busca_produto(
            db=db_session,
            coluna="nome",
            dado_busca="Mouse Logitech"
        )

        assert isinstance(resultado_busca, list)
        assert len(resultado_busca) > 0

    def test_editar_produto(self, db_session, produto_controller, produto_teste):
        """Testa edição de produto"""
        resultado = produto_controller.editar_produto(
            db=db_session,
            id_produto=produto_teste.codigo,
            valor=3800.00,
            nome="Notebook Dell Atualizado"
        )

        assert "sucesso" in resultado

        # Verificar alteração
        from src.database.models import Produtos
        produto_atualizado = db_session.query(Produtos).filter(
            Produtos.codigo == produto_teste.codigo
        ).first()

        assert float(produto_atualizado.valor) == 3800.00
        assert produto_atualizado.nome == "Notebook Dell Atualizado"
