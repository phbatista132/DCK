class TestFluxoCompletoEndToEnd:
    """
    Teste de cenário real completo:
    Simula um dia de operação da loja
    """

    def test_cenario_dia_de_loja(
            self,
            db_session,
            auth_controller,
            cliente_controller,
            produto_controller,
            estoque_controller,
            venda_controller
    ):
        """
        Cenário completo:
        1. Admin cria vendedor
        2. Vendedor faz login
        3. Gerente cadastra produtos
        4. Gerente repõe estoque
        5. Vendedor cadastra cliente
        6. Cliente faz compra
        7. Verificar estatísticas
        """

        print("\n=== INICIANDO CENÁRIO COMPLETO ===\n")

        # 1. SETUP: Criar usuários
        print("1️⃣ Criando usuários...")

        # Admin
        sucesso, _, admin = auth_controller.registrar_usuario(
            db=db_session,
            username="admin",
            email="admin@loja.com",
            senha="Admin123!@#",
            nome_completo="Administrador",
            tipo_usuario="admin"
        )
        assert sucesso
        print(f"   ✅ Admin criado: {admin['username']}")

        # Vendedor
        sucesso, _, vendedor = auth_controller.registrar_usuario(
            db=db_session,
            username="joao",
            email="joao@loja.com",
            senha="Joao123!@#",
            nome_completo="João Vendedor",
            tipo_usuario="vendedor"
        )
        assert sucesso
        print(f"   ✅ Vendedor criado: {vendedor['username']}")

        # 2. PRODUTOS: Cadastrar e repor estoque
        print("\n2️⃣ Cadastrando produtos...")

        # Produto 1
        resultado = produto_controller.cadastrar_produto(
            db=db_session,
            nome="Notebook Dell",
            modelo="Inspiron 15",
            categoria="Eletrônicos",
            valor=3500.00,
            quantidade_estoque=1,  # Vai repor depois
            vlr_compra=2800.00
        )
        assert "sucesso" in resultado

        # Produto 2
        resultado = produto_controller.cadastrar_produto(
            db=db_session,
            nome="Mouse Logitech",
            modelo="MX Master",
            categoria="Periféricos",
            valor=450.00,
            quantidade_estoque=1,
            vlr_compra=300.00
        )
        assert "sucesso" in resultado
        print("   ✅ 2 produtos cadastrados")

        # Repor estoque
        print("\n3️⃣ Repondo estoque...")
        from src.database.models import Produtos

        notebook = db_session.query(Produtos).filter(
            Produtos.nome == "Notebook Dell"
        ).first()

        mouse = db_session.query(Produtos).filter(
            Produtos.nome == "Mouse Logitech"
        ).first()

        estoque_controller.repor_estoque(
            db=db_session,
            id_item=notebook.codigo,
            qtd=9,
            usuario_id=admin['id_usuario']
        )

        estoque_controller.repor_estoque(
            db=db_session,
            id_item=mouse.codigo,
            qtd=49,
            usuario_id=admin['id_usuario']
        )
        print("   ✅ Estoque reposto")

        # 3. CLIENTE: Cadastrar
        print("\n4️⃣ Cadastrando cliente...")

        resultado = cliente_controller.cadastrar_cliente(
            db=db_session,
            cpf="49209207840",
            nome="Maria Cliente",
            dt_nascimento="10/05/1992",
            endereco="Rua das Flores, 100",
            telefone="11987654321"
        )
        assert "sucesso" in resultado
        print("   ✅ Cliente cadastrado")

        # 4. VENDA: Processo completo
        print("\n5️⃣ Iniciando processo de venda...")

        vendedor_id = vendedor['id_usuario']

        # Adicionar notebook
        sucesso, msg = venda_controller.adicionar_item_carrinho(
            db=db_session,
            usuario_id=vendedor_id,
            produto_id=notebook.codigo,
            quantidade=1
        )
        assert sucesso
        print(f"   ✅ Notebook adicionado ao carrinho")

        # Adicionar mouse
        sucesso, msg = venda_controller.adicionar_item_carrinho(
            db=db_session,
            usuario_id=vendedor_id,
            produto_id=mouse.codigo,
            quantidade=2
        )
        print(sucesso, msg)
        assert sucesso
        print(f"   ✅ Mouse adicionado ao carrinho")

        # Ver carrinho
        carrinho = venda_controller.ver_carrinho(db_session, vendedor_id)
        print(f"\n   📦 Carrinho:")
        print(f"      Total de itens: {carrinho.total_itens}")
        print(f"      Subtotal: R$ {carrinho.subtotal:.2f}")

        # Finalizar venda com desconto
        print("\n6️⃣ Finalizando venda...")

        sucesso, msg, dados_venda = venda_controller.finalizar_venda(
            db=db_session,
            usuario_id=vendedor_id,
            cpf_cliente="49209207840",
            forma_pagamento="Credito",
            percentual_desconto=15.0
        )
        print(sucesso, msg, dados_venda)
        assert sucesso
        print(f"   ✅ Venda finalizada!")
        print(f"      ID: {dados_venda['id_venda']}")
        print(f"      Subtotal: R$ {dados_venda['subtotal']:.2f}")
        print(f"      Desconto (15%): R$ {dados_venda['desconto']:.2f}")
        print(f"      Total: R$ {dados_venda['total']:.2f}")

        # 5. VALIDAÇÕES FINAIS
        print("\n7️⃣ Validando resultados...")

        # Verificar estoque
        db_session.refresh(notebook)
        db_session.refresh(mouse)

        assert notebook.quantidade_estoque == 9  # 10 - 1
        assert mouse.quantidade_estoque == 48  # 50 - 2
        print("   ✅ Estoque atualizado corretamente")

        # Verificar estatísticas
        stats = venda_controller.obter_estatisticas_vendas(
            db=db_session,
            vendedor_id=vendedor_id
        )

        assert stats['total_vendas'] == 1
        assert stats['valor_total'] > 0
        print(f"   ✅ Estatísticas:")
        print(f"      Total de vendas: {stats['total_vendas']}")
        print(f"      Valor total: R$ {stats['valor_total']:.2f}")
        print(f"      Ticket médio: R$ {stats['ticket_medio']:.2f}")

        print("\n=== CENÁRIO COMPLETO EXECUTADO COM SUCESSO! ===\n")
