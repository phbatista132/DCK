class TestClienteFlow:
    """Testes de fluxo de clientes"""

    def test_cadastro_e_busca_cliente(self, db_session, cliente_controller):
        """Testa cadastro e busca de cliente"""
        # 1. Cadastrar
        resultado = cliente_controller.cadastrar_cliente(
            db=db_session,
            cpf="98765432100",
            nome="Maria Santos",
            dt_nascimento="15/03/1985",
            endereco="Av. Paulista, 1000",
            telefone="11999887766"
        )

        assert "sucesso" in resultado

        # 2. Buscar
        cliente = cliente_controller.buscar_cliente(db_session, "98765432100")

        assert cliente is not None
        assert cliente.nome == "Maria Santos"
        assert cliente.ativo == True

    def test_editar_cliente(self, db_session, cliente_controller, cliente_teste):
        """Testa edição de dados do cliente"""
        resultado = cliente_controller.editar_cadastro(
            db=db_session,
            cpf=cliente_teste.cpf,
            telefone="11888776655",
            endereco="Nova Rua, 456"
        )

        assert "sucesso" in resultado

        # Verificar alteração
        cliente_atualizado = cliente_controller.buscar_cliente(
            db_session,
            cliente_teste.cpf
        )

        assert cliente_atualizado.telefone == "11888776655"
        assert cliente_atualizado.endereco == "Nova Rua, 456"

    def test_desativar_cliente(self, db_session, cliente_controller, cliente_teste):
        """Testa desativação de cliente"""
        resultado = cliente_controller.desativar_cliente(
            db_session,
            cliente_teste.cpf
        )

        assert "desativado" in resultado.lower()

        # Verificar desativação
        cliente = cliente_controller.buscar_cliente(db_session, cliente_teste.cpf)
        assert cliente.ativo == False