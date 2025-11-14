import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.controllers.auth_controller import AuthController
from src.controllers.cliente_controller import ClienteController
from src.controllers.produto_controller import ProdutoController
from src.controllers.estoque_controller import EstoqueController
from src.controllers.carrinho_controller import CarrinhoController
from src.controllers.venda_controller import VendaController


@pytest.fixture(scope="function")
def db_session():
    """
    Cria banco de dados em memória para cada teste
    Garante isolamento completo entre testes
    """
    # Criar engine em memória
    engine = create_engine('sqlite:///:memory:', echo=False)

    # Criar todas as tabelas
    Base.metadata.create_all(engine)

    # Criar sessão
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def auth_controller():
    """Fixture do AuthController"""
    return AuthController()


@pytest.fixture
def cliente_controller():
    """Fixture do ClienteController"""
    return ClienteController()


@pytest.fixture
def produto_controller():
    """Fixture do ProdutoController"""
    return ProdutoController()


@pytest.fixture
def estoque_controller():
    """Fixture do EstoqueController"""
    return EstoqueController()


@pytest.fixture
def carrinho_controller():
    """Fixture do CarrinhoController"""
    return CarrinhoController()


@pytest.fixture
def venda_controller():
    """Fixture do VendaController"""
    return VendaController()


@pytest.fixture
def usuario_admin(db_session, auth_controller):
    """Cria usuário admin para testes"""
    sucesso, msg, dados = auth_controller.registrar_usuario(
        db=db_session,
        username="admin_test",
        email="admin@test.com",
        senha="Admin123!@#",
        nome_completo="Administrador Teste",
        tipo_usuario="admin"
    )

    assert sucesso, f"Falha ao criar admin: {msg}"
    return dados


@pytest.fixture
def usuario_vendedor(db_session, auth_controller):
    """Cria usuário vendedor para testes"""
    sucesso, msg, dados = auth_controller.registrar_usuario(
        db=db_session,
        username="vendedor_test",
        email="vendedor@test.com",
        senha="Vendedor123!@#",
        nome_completo="Vendedor Teste",
        tipo_usuario="vendedor"
    )

    assert sucesso, f"Falha ao criar vendedor: {msg}"
    return dados


@pytest.fixture
def cliente_teste(db_session, cliente_controller):
    """Cria cliente para testes"""
    resultado = cliente_controller.cadastrar_cliente(
        db=db_session,
        cpf="49209207840",
        nome="Cliente Teste",
        dt_nascimento="01/01/1990",
        endereco="Rua Teste, 123",
        telefone="11987654321"
    )

    assert "sucesso" in resultado, f"Falha ao criar cliente: {resultado}"

    # Buscar cliente criado
    cliente = cliente_controller.buscar_cliente(db_session, "12345678900")
    return cliente


@pytest.fixture
def produto_teste(db_session, produto_controller):
    """Cria produto para testes"""
    resultado = produto_controller.cadastrar_produto(
        db=db_session,
        nome="Notebook Dell",
        modelo="Inspiron 15",
        categoria="Eletrônicos",
        valor=3500.00,
        quantidade=10,
        vlr_compra=2800.00
    )

    assert "sucesso" in resultado, f"Falha ao criar produto: {resultado}"

    # Buscar produto criado
    from src.database.models import Produtos
    produto = db_session.query(Produtos).filter(
        Produtos.nome == "Notebook Dell"
    ).first()

    return produto