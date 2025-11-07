import pandas as pd


class TestProdutoControllerCadastro:
    """Testes de cadastro de produto"""

    def test_cadastrar_produto_sucesso(self, produto_controller):
        """Testa cadastro com sucesso"""
        resultado = produto_controller.cadastrar_produto(
            nome="Notebook Dell",
            modelo="Inspiron 15",
            categoria="Eletrônicos",
            valor=3500.0,
            quantidade_estoque=10,
            vlr_compra=2800.0
        )

        assert resultado == "Produto cadastrado com sucesso"

        # Verificar geração de código
        assert produto_controller.gera_codigo() == 2

    def test_cadastrar_produto_valor_zero(self, produto_controller):
        """Testa rejeição de valor zero"""
        resultado = produto_controller.cadastrar_produto(
            "Teste", "Test", "Test", 0.0, 10, 50.0
        )

        assert "maior que zero" in resultado

    def test_cadastrar_produto_valor_negativo(self, produto_controller):
        """Testa rejeição de valor negativo"""
        resultado = produto_controller.cadastrar_produto(
            "Teste", "Test", "Test", -100.0, 10, 50.0
        )

        assert "maior que zero" in resultado

    def test_cadastrar_produto_vlr_compra_negativo(self, produto_controller):
        """Testa rejeição de valor de compra negativo"""
        resultado = produto_controller.cadastrar_produto(
            "Teste", "Test", "Test", 100.0, 10, -50.0
        )

        assert "maior que zero" in resultado

    def test_cadastrar_produto_quantidade_negativa(self, produto_controller):
        """Testa rejeição de quantidade negativa"""
        resultado = produto_controller.cadastrar_produto(
            "Teste", "Test", "Test", 100.0, -10, 50.0
        )

        assert "negativa" in resultado

    def test_cadastrar_produto_margem_negativa(self, produto_controller):
        """Testa rejeição quando valor < vlr_compra"""
        resultado = produto_controller.cadastrar_produto(
            "Teste","Teste", "Test", 80.0, 10, 100.0  # valor < vlr_compra
        )

        assert "maior que valor de compra" in resultado

    def test_cadastrar_produto_duplicado(self, produto_controller):
        """Testa rejeição de produto duplicado"""
        # Primeiro cadastro
        produto_controller.cadastrar_produto(
            "Mouse Logitech", "MX Master", "Periféricos", 250.0, 20, 180.0
        )

        # Segundo cadastro (duplicado)
        resultado = produto_controller.cadastrar_produto(
            "Mouse Logitech", "MX Master", "Periféricos", 260.0, 15, 180.0
        )

        assert "cadastrado" in resultado

    def test_gerar_codigo_sequencial(self, produto_controller):
        """Testa geração sequencial de códigos"""
        # Cadastrar 3 produtos
        produto_controller.cadastrar_produto("Produto 1", "M1", "Cat", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("Produto 2", "M2", "Cat", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("Produto 3", "M3", "Cat", 100.0, 10, 80.0)

        # Próximo código deve ser 4
        assert produto_controller.gera_codigo() == 4


class TestProdutoControllerEdicao:
    """Testes de edição de produto"""

    def test_editar_nome_sucesso(self, produto_controller, produto_cadastrado):
        """Testa edição de nome com sucesso"""
        resultado = produto_controller.editar_produto(
            produto_cadastrado,
            nome="Notebook Dell XPS"
        )

        assert resultado == "Produto editado com sucesso"

        # Verificar alteração
        df = pd.read_csv(produto_controller.produtos_data)
        nome = df[df['codigo'] == produto_cadastrado]['nome'].values[0]
        assert nome == "Notebook Dell XPS"

    def test_editar_valor_sucesso(self, produto_controller, produto_cadastrado):
        """Testa edição de valor com sucesso"""
        resultado = produto_controller.editar_produto(
            produto_cadastrado,
            valor=3800.0
        )

        assert resultado == "Produto editado com sucesso"

        # Verificar que margem foi recalculada
        df = pd.read_csv(produto_controller.produtos_data)
        margem = df[df['codigo'] == produto_cadastrado]['margem_lucro'].values[0]
        assert margem > 0  # Deve ter recalculado

    def test_editar_multiplos_campos(self, produto_controller, produto_cadastrado):
        """Testa edição de múltiplos campos"""
        resultado = produto_controller.editar_produto(
            produto_cadastrado,
            nome="Notebook Novo",
            valor=4000.0,
            vlr_compra=3200.0
        )

        assert resultado == "Produto editado com sucesso"

        # Verificar alterações
        df = pd.read_csv(produto_controller.produtos_data)
        produto = df[df['codigo'] == produto_cadastrado].iloc[0]
        assert produto['nome'] == "Notebook Novo"
        assert produto['valor'] == 4000.0
        assert produto['vlr_compra'] == 3200.0

    def test_editar_campo_nao_permitido(self, produto_controller, produto_cadastrado):
        """Testa rejeição de campo não permitido"""
        resultado = produto_controller.editar_produto(
            produto_cadastrado,
            codigo=999  # Código não deve ser editável
        )

        assert "não pode ser editado" in resultado

    def test_editar_valor_invalido(self, produto_controller, produto_cadastrado):
        """Testa rejeição de valor inválido"""
        resultado = produto_controller.editar_produto(
            produto_cadastrado,
            valor=-100.0
        )

        assert "maior que zero" in resultado

    def test_editar_produto_inexistente(self, produto_controller):
        """Testa edição de produto que não existe"""
        resultado = produto_controller.editar_produto(
            9999,
            nome="Produto Fantasma"
        )

        assert "não localizado" in resultado or "não encontrado" in resultado


class TestProdutoControllerBusca:
    """Testes de busca de produto"""

    def test_buscar_por_codigo(self, produto_controller, produto_cadastrado):
        """Testa busca por código"""
        resultado = produto_controller.busca_produto("codigo", produto_cadastrado)

        assert "Notebook Dell" in resultado
        assert "Inspiron 15" in resultado

    def test_buscar_por_nome(self, produto_controller, produto_cadastrado):
        """Testa busca por nome"""
        resultado = produto_controller.busca_produto("nome", "Notebook Dell")

        assert "Notebook Dell" in resultado

    def test_buscar_por_categoria(self, produto_controller, produto_cadastrado):
        """Testa busca por categoria"""
        resultado = produto_controller.busca_produto("categoria", "Eletrônicos")

        assert "Notebook Dell" in resultado

    def test_buscar_coluna_inexistente(self, produto_controller):
        """Testa busca em coluna que não existe"""
        resultado = produto_controller.busca_produto("coluna_invalida", "valor")

        assert "não localizada" in resultado

    def test_buscar_dado_inexistente(self, produto_controller, produto_cadastrado):
        """Testa busca de dado que não existe"""
        resultado = produto_controller.busca_produto("nome", "Produto Inexistente")

        assert "não localizado" in resultado


class TestProdutoControllerDesativacao:
    """Testes de desativação de produto"""

    def test_desabilitar_produto_sucesso(self, produto_controller, produto_cadastrado):
        """Testa desativação com sucesso"""
        resultado = produto_controller.desabilitar_produto(produto_cadastrado)

        assert resultado == "Produto desativado com sucesso"

        # Verificar que foi desativado
        df = pd.read_csv(produto_controller.produtos_data)
        ativo = df[df['codigo'] == produto_cadastrado]['ativo'].values[0]
        assert ativo == False

    def test_desabilitar_produto_inexistente(self, produto_controller):
        """Testa desativação de produto que não existe"""
        resultado = produto_controller.desabilitar_produto(9999)

        assert "não encontrado" in resultado or "não localizado" in resultado


class TestProdutoControllerFiltros:
    """Testes de filtros e relatórios"""

    def test_filtro_categoria(self, produto_controller):
        """Testa filtro por categoria"""
        # Cadastrar produtos de categorias diferentes
        produto_controller.cadastrar_produto("Notebook", "Dell", "Eletrônicos", 3000.0, 5, 2500.0)
        produto_controller.cadastrar_produto("Mouse", "Logitech", "Periféricos", 80.0, 20, 50.0)
        produto_controller.cadastrar_produto("Teclado", "Razer", "Periféricos", 200.0, 15, 150.0)

        # Filtrar por Periféricos
        resultado = produto_controller.filtro_categoria("Periféricos")

        assert "Mouse" in resultado
        assert "Teclado" in resultado
        assert "Notebook" not in resultado

    def test_filtro_categoria_vazia(self, produto_controller, produto_cadastrado):
        """Testa filtro de categoria sem produtos"""
        resultado = produto_controller.filtro_categoria("Categoria Inexistente")

        assert "Nenhum produto encontrado" in resultado

    def test_total_produtos(self, produto_controller):
        """Testa contagem total de produtos"""
        # Cadastrar 3 produtos
        produto_controller.cadastrar_produto("Produto 1", "M1", "Cat", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("Produto 2", "M2", "Cat", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("Produto 3", "M3", "Cat", 100.0, 10, 80.0)

        resultado = produto_controller.total_produtos()

        assert "3" in resultado

    def test_produtos_por_categoria(self, produto_controller):
        """Testa distribuição de produtos por categoria"""
        # Cadastrar produtos
        produto_controller.cadastrar_produto("P1", "M1", "Eletrônicos", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("P2", "M2", "Eletrônicos", 100.0, 10, 80.0)
        produto_controller.cadastrar_produto("P3", "M3", "Periféricos", 100.0, 10, 80.0)

        resultado = produto_controller.produtos_categoria()

        assert "Eletrônicos" in resultado
        assert "Periféricos" in resultado
        assert "2 Produtos" in resultado  # Eletrônicos
        assert "1 Produtos" in resultado  # Periféricos


class TestProdutoControllerIntegracao:
    """Testes de integração do ProdutoController"""

    def test_fluxo_completo_produto(self, produto_controller):
        """Testa fluxo completo: cadastrar → editar → buscar → desativar"""
        # 1. Cadastrar
        resultado = produto_controller.cadastrar_produto(
            "Produto Teste",
            "Modelo X",
            "Categoria Y",
            500.0,
            20,
            400.0
        )
        assert "sucesso" in resultado

        # 2. Editar
        codigo = 1
        resultado = produto_controller.editar_produto(
            codigo,
            nome="Produto Editado",
            valor=600.0
        )
        assert "sucesso" in resultado

        # 3. Buscar
        resultado = produto_controller.busca_produto("nome", "Produto Editado")
        assert "Produto Editado" in resultado
        assert "600" in resultado

        # 4. Desabilitar
        resultado = produto_controller.desabilitar_produto(codigo)
        assert "sucesso" in resultado

        # 5. Verificar desativado
        df = pd.read_csv(produto_controller.produtos_data)
        ativo = df[df['codigo'] == codigo]['ativo'].values[0]
        assert ativo == False