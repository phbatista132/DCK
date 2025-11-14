import pytest
import tempfile
import os
from pathlib import Path
from src.controllers.cliente_controller import ClienteController
from src.controllers.estoque_controller import EstoqueController
from src.controllers.produto_controller import ProdutoController
from src.controllers.venda_controller import VendaController


@pytest.fixture
def temp_clientes_file():
    """Cria arquivo temporário JSONL para clientes"""
    fd, path = tempfile.mkstemp(suffix='.jsonl')
    os.close(fd)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_produtos_file():
    """Cria arquivo CSV temporário para produtos"""
    fd, path = tempfile.mkstemp(suffix='.csv')

    # Escreve header
    with os.fdopen(fd, 'w') as f:
        f.write("nome,modelo,categoria,valor,codigo,quantidade_estoque,dt_cadastro,vlr_compra,margem_lucro,ativo\n")

    yield path

    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_vendas_file():
    """Cria arquivo CSV temporário para vendas"""
    fd, path = tempfile.mkstemp(suffix='.csv')

    with os.fdopen(fd, 'w') as f:
        f.write("id_venda,database,cliente_id,itens,subtotal,total,desconto,forma_pagamento,status,data_finalizacao\n")

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_itens_vendas_file():
    """Cria arquivo CSV temporário para itens de vendas"""
    fd, path = tempfile.mkstemp(suffix='.csv')

    with os.fdopen(fd, 'w') as f:
        f.write("id_item,id_venda,produto_id,nome_produto,quantidade,preco_unitario,subtotal\n")

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def cliente_controller(temp_clientes_file):
    """Controller de Cliente com arquivo temporário"""
    controller = ClienteController()
    controller.cliente_data = Path(temp_clientes_file)
    return controller


@pytest.fixture
def produto_controller(temp_produtos_file):
    """Controller de Produto com arquivo temporário"""
    controller = ProdutoController()
    controller.produtos_data = Path(temp_produtos_file)
    return controller


@pytest.fixture
def estoque_controller(temp_produtos_file):
    """Controller de Estoque com arquivo temporário"""
    controller = EstoqueController()
    controller.estoque_data = Path(temp_produtos_file)
    return controller



@pytest.fixture
def venda_controller(temp_produtos_file, temp_vendas_file, temp_itens_vendas_file, temp_clientes_file):
    """Controller de Venda com arquivos temporários"""
    controller = VendaController()
    controller.estoque_data = Path(temp_produtos_file)
    controller.vendas_data = Path(temp_vendas_file)
    controller.itens_venda_data = Path(temp_itens_vendas_file)
    controller.estoque.estoque_data = Path(temp_produtos_file)
    controller.cliente.cliente_data = Path(temp_clientes_file)
    return controller


@pytest.fixture
def produto_cadastrado(produto_controller):
    """Fixture que retorna produto já cadastrado"""
    produto_controller.cadastrar_produto(
        nome="Notebook Dell",
        modelo="Inspiron 15",
        categoria="Eletrônicos",
        valor=3000.0,
        quantidade_estoque=10,
        vlr_compra=2500.0
    )
    return 1  # código do produto


@pytest.fixture
def cliente_cadastrado(cliente_controller):
    """Fixture que retorna cliente já cadastrado"""
    cliente_controller.cadastrar_cliente(
        nome="João Silva",
        dt_nascimento="15/05/1990",
        cpf="49209207840",
        endereco="Rua Test, 123",
        telefone="(11) 98765-4321"
    )
    return "49209207840"  # CPF do cliente