class TestVendaFlow:
    """Testes de fluxo completo de venda"""

    def test_fluxo_venda_completo(
            self,
            db_session,
            venda_controller,
            usuario_vendedor,
            cliente_teste,
            produto_teste
    ):
        """
        Testa fluxo completo:
        1. Adicionar itens ao carrinho
        2. Visualizar carrinho
        3. Alterar quantidade
        4. Finalizar venda
        5. Verificar baixa no estoque
        """
        vendedor_id = usuario_vendedor['id_usuario']

        # 1. Adicionar itens ao carrinho
        sucesso, msg = venda_controller.adicionar_item_carrinho(
            db=db_session,
            usuario_id=vendedor_id,
            produto_id=produto_teste.codigo,
            quantidade=2
        )

        assert sucesso, f"Falha ao adicionar item: {msg}"

        # 2. Visualizar carrinho
        carrinho = venda_controller.ver_carrinho(db_session, vendedor_id)

        assert carrinho is not None
        assert len(carrinho.itens) == 1
        assert carrinho.itens[0].quantidade == 2

        # 3. Alterar quantidade
        sucesso, msg = venda_controller.alterar_quantidade_carrinho(
            db=db_session,
            usuario_id=vendedor_id,
            produto_id=produto_teste.codigo,
            nova_quantidade=3
        )

        assert sucesso

        # Verificar alteração
        db_session.refresh(carrinho)
        assert carrinho.itens[0].quantidade == 3

        # Guardar estoque antes da venda
        estoque_antes = produto_teste.quantidade_estoque

        # 4. Finalizar venda
        sucesso, msg, dados_venda = venda_controller.finalizar_venda(
            db=db_session,
            usuario_id=vendedor_id,
            cpf_cliente=cliente_teste.cpf,
            forma_pagamento="Credito",
            percentual_desconto=10.0
        )

        assert sucesso, f"Falha ao finalizar venda: {msg}"
        assert dados_venda is not None
        assert 'id_venda' in dados_venda

        # 5. Verificar baixa no estoque
        db_session.refresh(produto_teste)
        assert produto_teste.quantidade_estoque == estoque_antes - 3

        # 6. Verificar que carrinho foi finalizado
        db_session.refresh(carrinho)
        assert carrinho.status == 'FINALIZADO'

    def test_cancelar_venda(
            self,
            db_session,
            venda_controller,
            usuario_vendedor,
            produto_teste
    ):
        """Testa cancelamento de venda"""
        vendedor_id = usuario_vendedor['id_usuario']

        # 1. Criar venda
        venda_controller.adicionar_item_carrinho(
            db=db_session,
            usuario_id=vendedor_id,
            produto_id=produto_teste.codigo,
            quantidade=2
        )

        estoque_antes = produto_teste.quantidade_estoque

        sucesso, msg, dados_venda = venda_controller.finalizar_venda(
            db=db_session,
            usuario_id=vendedor_id,
            forma_pagamento="Debito"
        )

        assert sucesso
        id_venda = dados_venda['id_venda']

        # 2. Cancelar venda
        sucesso, msg = venda_controller.cancelar_venda(
            db=db_session,
            id_venda=id_venda,
            motivo="Teste de cancelamento",
            usuario_id=vendedor_id
        )

        assert sucesso, f"Falha ao cancelar: {msg}"

        # 3. Verificar devolução ao estoque
        db_session.refresh(produto_teste)
        assert produto_teste.quantidade_estoque == estoque_antes
