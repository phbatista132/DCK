from src.controllers.produto_controller import ProdutoController
from src.controllers.estoque_controller import EstoqueController
from utils import logger
import logging


def main():
    sisproduto = ProdutoController()
    sisestoque = EstoqueController()
    while True:
        try:
            opc = int(input('Opção: '))
            if opc == 1:
                nome = str(input('Nome: '))
                modelo = str(input('Modelo: '))
                categoria = str(input('categoria: '))
                valor = float(input("Valor: ").replace(',', '.'))
                quantidade = int(input('Quantidade: '))
                vl_compra = float(input('Valor compra: ').replace(',', '.'))
                print(sisproduto.cadastrar_produto(nome, modelo, categoria, valor , quantidade, vl_compra))
            elif opc == 2:
                id_produto = int(input('ID: '))
                coluna = str(input('Coluna: '))
                dado = input('dado para alteração: ')
                sisproduto.editar_produto(id_produto, coluna, dado)

            elif opc == 3:
                coluna =  str(input('Filtra por: '))
                dado_busca = input('Produto: ')
                print(sisproduto.busca_produto(coluna, dado_busca))
            elif opc == 4:
                produto = int(input('ID Produto: '))
                quantidade = int(input('Quantidade para venda: '))
                print(sisestoque.disponibilidade(produto, quantidade))

            elif opc == 5:
                print(sisproduto.total_produtos())
            elif opc == 0:
                print('Saindo do programa!')
                break
            else:
                print('Opção não localizada')

        except Exception as e:
            print(f"Erro:  {e}")



if __name__ == '__main__':
    logger.setup()
    logger = logging.getLogger("produto_log")
    logger.debug("msg")
    logger.info("msg")
    logger.warning("msg")
    logger.error("msg")
    logger.critical("msg")
