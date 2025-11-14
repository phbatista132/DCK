class TestEstoqueFlow:
    """Testes de fluxo de estoque"""

    def test_reposicao_estoque(self, db_session, estoque_controller, produto_teste):
        """Testa reposição de estoque"""
        estoque_inicial = produto_teste.quantidade_estoque

        resultado = estoque_controller.repor_estoque(
            db=db_session,
            id_item=produto_teste.codigo,
            qtd=50,
            usuario_id=1
        )

        assert "sucesso" in resultado

        # Verificar reposição
        db_session.refresh(produto_teste)
        assert produto_teste.quantidade_estoque == estoque_inicial + 50

    def test_reserva_e_liberacao(
            self,
            db_session,
            estoque_controller,
            produto_teste,
            usuario_vendedor
    ):
        """Testa reserva e liberação de estoque"""
        # 1. Reservar
        sucesso, reserva_id = estoque_controller.reservar_estoque(
            db=db_session,
            produto_id=produto_teste.codigo,
            quantidade=5,
            usuario_id=usuario_vendedor['id_usuario']
        )

        assert sucesso
        assert reserva_id is not None

        # Verificar que foi reservado
        db_session.refresh(produto_teste)
        assert produto_teste.quantidade_reservada == 5

        # 2. Liberar
        sucesso, msg = estoque_controller.liberar_reserva(
            db=db_session,
            reserva_id=reserva_id
        )

        assert sucesso

        # Verificar que foi liberado
        db_session.refresh(produto_teste)
        assert produto_teste.quantidade_reservada == 0

    def test_verificar_disponibilidade(
            self,
            db_session,
            estoque_controller,
            produto_teste,
            usuario_vendedor
    ):
        """Testa verificação de disponibilidade"""
        # Reservar 5 unidades
        estoque_controller.reservar_estoque(
            db=db_session,
            produto_id=produto_teste.codigo,
            quantidade=5,
            usuario_id=usuario_vendedor['id_usuario']
        )

        # Verificar disponibilidade
        disponivel, qtd = estoque_controller.verificar_disponibilidade(
            db=db_session,
            produto_id=produto_teste.codigo,
            quantidade=3
        )

        assert disponivel
        assert qtd == 5

