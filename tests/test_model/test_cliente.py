import pytest
from datetime import date, datetime
from src.models.cliente import Cliente


class TestClienteModel:
    """Testes unitários do Model Cliente"""

    def test_criar_cliente_valido(self, data_nascimento_maior_idade):
        """Testa criação de cliente com dados válidos"""
        cliente = Cliente(
            id_cliente=1,
            nome="João Silva Santos",
            cpf="12345678900",
            dt_nascimento=data_nascimento_maior_idade,
            telefone="(11) 98765-4321",
            endereco="Rua Example, 123 - São Paulo/SP",
            ativo=True
        )

        assert cliente.id_cliente == 1
        assert cliente.nome == "João Silva Santos"
        assert cliente.cpf == "12345678900"
        assert cliente.dt_nascimento == data_nascimento_maior_idade
        assert cliente.telefone == "(11) 98765-4321"
        assert cliente.endereco == "Rua Example, 123 - São Paulo/SP"
        assert cliente.ativo is True
        assert cliente.data_cadastro is not None

    def test_criar_cliente_data_cadastro_automatica(self):
        """Testa criação automática de data_cadastro"""
        cliente = Cliente(
            id_cliente=1,
            nome="Maria Santos",
            cpf="98765432100",
            dt_nascimento=date(1985, 6, 15),
            telefone="(21) 91234-5678",
            endereco="Av. Test, 456",
            ativo=True
        )

        assert cliente.data_cadastro == date.today()

    def test_normalizar_cpf_com_formatacao(self):
        """Testa normalização de CPF com formatação"""
        cliente = Cliente(
            id_cliente=1,
            nome="Pedro Costa",
            cpf="123.456.789-00",  # Com formatação
            dt_nascimento=date(1992, 3, 10),
            telefone="(31) 99876-5432",
            endereco="Rua Test, 789",
            ativo=True
        )

        # CPF deve estar normalizado (só números)
        assert cliente.cpf == "12345678900"


    def test_rejeitar_nome_curto(self):
        """Testa rejeição de nome com menos de 3 caracteres"""
        with pytest.raises(ValueError, match="Nome deve conter 3 caracteres no minimo"):
            Cliente(
                id_cliente=1,
                nome="Jo",  # Menos de 3 caracteres
                cpf="12345678900",
                dt_nascimento=date(1990, 1, 1),
                telefone="(11) 98765-4321",
                endereco="Rua Test",
                ativo=True
            )

    def test_rejeitar_cpf_invalido_tamanho(self):
        """Testa rejeição de CPF com tamanho inválido"""
        with pytest.raises(ValueError, match="CPF deve ter 11 dígitos"):
            data_nascimento = "01/01/1990"
            Cliente(
                id_cliente=1,
                nome="Teste Silva",
                cpf="123456789",  # Menos de 11 dígitos
                dt_nascimento= datetime.strptime(data_nascimento, "%d/%m/%Y").date(),
                telefone="(11) 98765-4321",
                endereco="Rua Test",
                ativo=True
            )

    def test_calcular_idade_corretamente(self):
        """Testa cálculo de idade"""
        cliente = Cliente(
            id_cliente=1,
            nome="Ana Paula",
            cpf="12345678900",
            dt_nascimento=datetime.strptime("20/05/1990", "%d/%m/%Y").date(),
            telefone="(11) 98765-4321",
            endereco="Rua Test",
            ativo=True
        )

        idade = cliente.calcular_idade()

        # Idade deve ser 34 ou 35 dependendo se já passou o aniversário
        assert idade in [34, 35]

    def test_maior_idade_verdadeiro(self, data_nascimento_maior_idade):
        """Testa verificação de maioridade (True)"""
        cliente = Cliente(
            id_cliente=1,
            nome="Carlos Eduardo",
            cpf="12345678900",
            dt_nascimento=data_nascimento_maior_idade,
            telefone="(11) 98765-4321",
            endereco="Rua Test",
            ativo=True
        )
        assert cliente.maior_idade() is True

    def test_maior_idade_falso(self, data_nascimento_menor_idade):
        """Testa verificação de maioridade (False)"""
        cliente = Cliente(
            id_cliente=1,
            nome="Junior Silva",
            cpf="12345678900",
            dt_nascimento=data_nascimento_menor_idade,
            telefone="(11) 98765-4321",
            endereco="Rua Test",
            ativo=True
        )

        assert cliente.maior_idade() is False

    def test_desativar_cliente(self):
        """Testa desativação de cliente"""
        cliente = Cliente(
            id_cliente=1,
            nome="Teste Desativar",
            cpf="12345678900",
            dt_nascimento=date(1990, 1, 1),
            telefone="(11) 98765-4321",
            endereco="Rua Test",
            ativo=True
        )

        assert cliente.ativo is True
        cliente.desativar()
        assert cliente.ativo is False

    def test_esta_ativo(self):
        """Testa verificação de cliente ativo"""
        cliente = Cliente(
            id_cliente=1,
            nome="Teste Ativo",
            cpf="12345678900",
            dt_nascimento=date(1990, 1, 1),
            telefone="(11) 98765-4321",
            endereco="Rua Test",
            ativo=True
        )

        assert cliente.esta_ativo() is True
        cliente.desativar()
        assert cliente.esta_ativo() is False


    def test_to_dict(self):
        """Testa conversão para dicionário"""
        cliente = Cliente(
            id_cliente=1,
            nome="Fernanda Lima",
            cpf="12345678900",
            dt_nascimento=datetime.strptime("27/07/1988", "%d/%m/%Y").date(),
            telefone="(41) 97777-8888",
            endereco="Rua Conversão, 999",
            ativo=True
        )

        dict_cliente = cliente.to_dict()

        assert isinstance(dict_cliente, dict)
        assert dict_cliente['id_cliente'] == 1
        assert dict_cliente['nome'] == "Fernanda Lima"
        assert dict_cliente['cpf'] == "12345678900"
        assert dict_cliente['dt_nascimento'] == "27/07/1988"
        assert dict_cliente['telefone'] == "(41) 97777-8888"
        assert dict_cliente['endereco'] == "Rua Conversão, 999"
        assert dict_cliente['ativo'] is True

    def test_from_dict(self):
        """Testa criação a partir de dicionário"""
        dados = {
            'id_cliente': 1,
            'nome': "Roberto Carlos",
            'cpf': "98765432100",
            'dt_nascimento': "31/12/1985",
            'telefone': "(51) 96666-7777",
            'endereco': "Av. From Dict, 777",
            'ativo': True,
            'data_cadastro': "2025-01-01"
        }

        cliente = Cliente.from_dict(dados)

        assert cliente.id_cliente == 1
        assert cliente.nome == "Roberto Carlos"
        assert cliente.cpf == "98765432100"
        assert cliente.dt_nascimento == date(1985, 12, 31)
        assert cliente.telefone == "(51) 96666-7777"
        assert cliente.endereco == "Av. From Dict, 777"
        assert cliente.ativo is True
        assert cliente.data_cadastro == date(2025, 1, 1)

    def test_to_dict_from_dict_simetrico(self):
        """Testa simetria entre to_dict e from_dict"""
        cliente_original = Cliente(
            id_cliente=1,
            nome="Simetria Teste",
            cpf="11122233344",
            dt_nascimento=date(1995, 8, 15),
            telefone="(61) 95555-4444",
            endereco="Rua Simetria, 321",
            ativo=True
        )

        dict_cliente = cliente_original.to_dict()
        cliente_recuperado = Cliente.from_dict(dict_cliente)

        assert cliente_original.id_cliente == cliente_recuperado.id_cliente
        assert cliente_original.nome == cliente_recuperado.nome
        assert cliente_original.cpf == cliente_recuperado.cpf
        assert cliente_original.dt_nascimento == cliente_recuperado.dt_nascimento
        assert cliente_original.telefone == cliente_recuperado.telefone
        assert cliente_original.endereco == cliente_recuperado.endereco
        assert cliente_original.ativo == cliente_recuperado.ativo

    def test_str_formatacao(self):
        """Testa formatação string do cliente"""
        cliente = Cliente(
            id_cliente=1,
            nome="String Test",
            cpf="12345678900",
            dt_nascimento=date(1990, 1, 1),
            telefone="(11) 98765-4321",
            endereco="Rua Test",
            ativo=True
        )

        str_cliente = str(cliente)

        assert "String Test" in str_cliente
        assert "12345678900" in str_cliente
        assert "(11) 98765-4321" in str_cliente

    # ==================== TESTES DE MEMÓRIA ====================

    @pytest.mark.memory
    def test_tamanho_objeto_cliente(self):
        """Testa tamanho do objeto Cliente em memória"""
        from pympler import asizeof

        cliente = Cliente(
            id_cliente=1,
            nome="João da Silva Santos Junior",
            cpf="12345678900",
            dt_nascimento=date(1990, 1, 1),
            telefone="(11) 98765-4321",
            endereco="Rua Example Longa, 123 - Bairro Test - São Paulo/SP - CEP 01234-567",
            ativo=True
        )

        tamanho = asizeof.asizeof(cliente)
        tamanho_kb = tamanho / 1024

        print(f"\n🔍 Tamanho Cliente: {tamanho} bytes ({tamanho_kb:.2f} KB)")

        # Cliente deve ocupar menos de 1 KB
        assert tamanho < 1024, f"Cliente muito grande: {tamanho} bytes"


class TestClienteIntegration:
    """Testes de integração do Cliente"""

    def test_criar_multiplos_clientes(self):
        """Testa criação de múltiplos clientes"""
        clientes = []

        for i in range(50):
            cliente = Cliente(
                id_cliente=i,
                nome=f"Cliente {i}",
                cpf=f"{i:011d}",  # CPF formatado com zeros à esquerda
                dt_nascimento=date(1990, 1, 1),
                telefone=f"(11) 9{i:04d}-{i:04d}",
                endereco=f"Rua {i}, {i}",
                ativo=True
            )
            clientes.append(cliente)

        assert len(clientes) == 50
        assert all(c.esta_ativo() for c in clientes)
        assert all(c.maior_idade() for c in clientes)

    @pytest.mark.memory
    def test_memoria_100_clientes(self):
        """Testa consumo de memória com 100 clientes"""
        from pympler import asizeof

        clientes = [
            Cliente(
                id_cliente=i,
                nome=f"Cliente Teste {i}",
                cpf=f"{i:011d}",
                dt_nascimento=date(1990, 1, 1),
                telefone=f"(11) 9{i:04d}-{i:04d}",
                endereco=f"Rua Test {i}, {i}",
                ativo=True
            )
            for i in range(100)
        ]

        tamanho_total = asizeof.asizeof(clientes)
        tamanho_mb = tamanho_total / (1024 * 1024)

        print(f"\n🔍 100 Clientes: {tamanho_mb:.2f} MB")

        # 100 clientes devem ocupar menos de 0.5 MB
        assert tamanho_mb < 0.5, f"100 clientes ocupam {tamanho_mb:.2f} MB"