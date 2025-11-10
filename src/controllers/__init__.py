#imports para os controladores
from src.controllers.estoque_controller import EstoqueController
from src.controllers.produto_controller import ProdutoController
from src.controllers.cliente_controller import ClienteController
from src.controllers.auth_controller import AuthController

__all__ = ['EstoqueController', 'ClienteController', 'ProdutoController', "AuthController"]