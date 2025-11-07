class TestClienteControllerCadastro:
    """Testes de cadastro de cliente"""

    def test_cadastrar_cliente_sucesso(self, cliente_controller):
        """Testa cadastro de cliente com sucesso"""
        resultado = cliente_controller.cadastrar_cliente(
            nome="João Silva Santos",
            dt_nascimento="15/05/1990",
            cpf="49209207840",
            endereco="Rua Example, 123 - São Paulo/SP",
            telefone="(11) 98765-4321"
        )

        assert resultado == "Cliente cadastrado com sucesso"

        # Verificar se foi salvo
        cliente = cliente_controller.buscar_cliente(cpf="49209207840")
        assert cliente is not None
        assert cliente.nome == "João Silva Santos"
        assert cliente.cpf == "49209207840"  # CPF normalizado

    def test_cadastrar_cliente_cpf_invalido(self, cliente_controller):
        """Testa rejeição de CPF inválido"""
        resultado = cliente_controller.cadastrar_cliente(
            nome="Teste",
            dt_nascimento="01/01/1990",
            cpf="111.111.111-11",  # CPF inválido
            endereco="Rua Test",
            telefone="(11) 99999-9999"
        )

        assert "incorreto" in resultado or "invalido" in resultado

    def test_cadastrar_cliente_menor_idade(self, cliente_controller):
        """Testa rejeição de menor de idade"""
        resultado = cliente_controller.cadastrar_cliente(
            nome="Junior Silva",
            dt_nascimento="01/01/2010",  # Menor de idade
            cpf="49209207840",
            endereco="Rua Test",
            telefone="(11) 99999-9999"
        )

        assert "menor de idade" in resultado

    def test_cadastrar_cliente_duplicado(self, cliente_controller):
        """Testa rejeição de cliente duplicado"""
        cpf = "49209207840"

        # Primeiro cadastro
        cliente_controller.cadastrar_cliente(
            "Cliente 1", "01/01/1990", cpf, "Rua", "(11) 99999-9999"
        )

        # Segundo cadastro (duplicado)
        resultado = cliente_controller.cadastrar_cliente(
            "Cliente 2", "01/01/1990", cpf, "Rua", "(11) 99999-9999"
        )

        assert "cadastrado" in resultado

    def test_gerar_id_sequencial(self, cliente_controller):
        """Testa geração sequencial de IDs"""
        # Cadastrar 3 clientes
        cliente_controller.cadastrar_cliente("Cliente 1", "01/01/1990", "49209207840", "Rua 1", "(11) 91111-1111")
        cliente_controller.cadastrar_cliente("Cliente 2", "02/02/1991", "08781017804", "Rua 2", "(11) 92222-2222")
        cliente_controller.cadastrar_cliente("Cliente 3", "03/03/1992", "73263052187", "Rua 3", "(11) 93333-3333")

        # Verificar IDs
        c1 = cliente_controller.buscar_cliente("49209207840")
        c2 = cliente_controller.buscar_cliente("08781017804")
        c3 = cliente_controller.buscar_cliente("73263052187")

        assert c1.id_cliente == 1
        assert c2.id_cliente == 2
        assert c3.id_cliente == 3


class TestClienteControllerBusca:
    """Testes de busca de cliente"""

    def test_buscar_cliente_existente(self, cliente_controller, cliente_cadastrado):
        """Testa busca de cliente existente"""
        cliente = cliente_controller.buscar_cliente(cpf=cliente_cadastrado)

        assert cliente is not None
        assert cliente.nome == "João Silva"
        assert cliente.cpf == cliente_cadastrado
        assert cliente.esta_ativo() is True

    def test_buscar_cliente_inexistente(self, cliente_controller):
        """Testa busca de cliente que não existe"""
        cliente = cliente_controller.buscar_cliente(cpf="00000000000")

        assert cliente is None

    def test_buscar_em_arquivo_vazio(self, cliente_controller):
        """Testa busca em arquivo vazio"""
        cliente = cliente_controller.buscar_cliente(cpf="12345678900")

        assert cliente is None


class TestClienteControllerEdicao:
    """Testes de edição de cliente"""

    def test_editar_telefone_sucesso(self, cliente_controller, cliente_cadastrado):
        """Testa edição de telefone com sucesso"""
        resultado = cliente_controller.editar_cadastro(
            cliente_cadastrado,
            telefone="(11) 91111-2222"
        )

        assert resultado == "Dados alterados com sucesso"

        cliente = cliente_controller.buscar_cliente(cliente_cadastrado)
        assert cliente.telefone == "(11) 91111-2222"

    def test_editar_endereco_sucesso(self, cliente_controller, cliente_cadastrado):
        """Testa edição de endereço com sucesso"""
        resultado = cliente_controller.editar_cadastro(
            cliente_cadastrado,
            endereco="Av Nova, 456 - SP"
        )

        assert resultado == "Dados alterados com sucesso"

        cliente = cliente_controller.buscar_cliente(cliente_cadastrado)
        assert cliente.endereco == "Av Nova, 456 - SP"

    def test_editar_telefone_e_endereco(self, cliente_controller, cliente_cadastrado):
        """Testa edição de múltiplos campos"""
        resultado = cliente_controller.editar_cadastro(
            cliente_cadastrado,
            telefone="(11) 91111-2222",
            endereco="Av Nova, 456"
        )

        assert resultado == "Dados alterados com sucesso"

        cliente = cliente_controller.buscar_cliente(cliente_cadastrado)
        assert cliente.telefone == "(11) 91111-2222"
        assert cliente.endereco == "Av Nova, 456"

    def test_editar_campo_nao_permitido(self, cliente_controller, cliente_cadastrado):
        """Testa rejeição de campo não permitido"""
        resultado = cliente_controller.editar_cadastro(
            cliente_cadastrado,
            nome="Nome Novo"  # Nome não é permitido
        )

        assert "não pemitido" in resultado or "não permitido" in resultado

    def test_editar_cliente_inexistente(self, cliente_controller):
        """Testa edição de cliente que não existe"""
        resultado = cliente_controller.editar_cadastro(
            "00000000000",
            telefone="(11) 99999-9999"
        )

        assert resultado == "Cliente não encontrado"


class TestClienteControllerDesativacao:
    """Testes de desativação de cliente"""

    def test_desativar_cliente_sucesso(self, cliente_controller, cliente_cadastrado):
        """Testa desativação com sucesso"""
        resultado = cliente_controller.desativar_cliente(cliente_cadastrado)

        assert resultado == "Cliente desativado"

        cliente = cliente_controller.buscar_cliente(cliente_cadastrado)
        assert cliente.ativo is False

    def test_desativar_cliente_inexistente(self, cliente_controller):
        """Testa desativação de cliente que não existe"""
        resultado = cliente_controller.desativar_cliente("00000000000")

        assert resultado == "Cliente não encontrado"


class TestClienteControllerListagem:
    """Testes de listagem de clientes"""

    def test_listar_clientes_ativos(self, cliente_controller):
        """Testa listagem de clientes ativos"""
        # Cadastrar 3 clientes
        cliente_controller.cadastrar_cliente("Cliente 1", "01/01/1990", "49209207840", "Rua 1", "(11) 91111-1111")
        cliente_controller.cadastrar_cliente("Cliente 2", "02/02/1991", "08781017804", "Rua 2", "(11) 92222-2222")
        cliente_controller.cadastrar_cliente("Cliente 3", "03/03/1992", "73263052187", "Rua 3", "(11) 93333-3333")

        # Desativar um
        cliente_controller.desativar_cliente("08781017804")

        # Listar
        clientes = cliente_controller.listar_clientes()

        assert len(clientes) == 2  # Apenas os ativos
        assert all(c.esta_ativo() for c in clientes)
        assert all(c.cpf != "08781017804" for c in clientes)

    def test_listar_arquivo_vazio(self, cliente_controller):
        """Testa listagem com arquivo vazio"""
        resultado = cliente_controller.listar_clientes()

        assert resultado == "Sem clientes cadastrados"

    def test_listar_todos_inativos(self, cliente_controller):
        """Testa listagem quando todos estão inativos"""
        # Cadastrar e desativar
        cliente_controller.cadastrar_cliente("Cliente 1", "01/01/1990", "49209207840", "Rua 1", "(11) 91111-1111")
        cliente_controller.desativar_cliente("49209207840")

        # Listar
        clientes = cliente_controller.listar_clientes()

        assert len(clientes) == 0