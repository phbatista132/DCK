from src.controllers.produto_controller import ProdutoController
from src.controllers.venda_controller import VendaController
from src.controllers.cliente_controller import ClienteController


def main():
    sisproduto = ProdutoController()
    sisvendas = VendaController()
    siscliente = ClienteController()
    while True:
        try:
            opc = int(input("OPÇÃO: "))
            if opc == 1:
                produto = int(input("Produto: "))
                quantidade = int(input("Quantidade: "))
                print(sisvendas.adicionar_item(produto, quantidade))
            elif opc == 2:
                produto = int(input("Produto: "))
                nova_quantidade = int(input("Quantidade: "))
                print(sisvendas.alterar_quantidade(produto, nova_quantidade))
            elif opc == 3:
                produto = int(input("Produto: "))
                print(sisvendas.remover_item(produto))
            elif opc == 4:
                print(sisvendas.ver_carinho())
            elif opc == 5:
                cliente = input("CPF: ")
                forma_pagamento = input('Forma de pagamento: ')
                desconto = float(input("Desconto: "))
                print(sisvendas.finalizar_venda(cliente ,forma_pagamento=forma_pagamento, percentual_desconto=desconto))
            elif opc == 6:
                print(sisvendas.cancelar_venda())
            elif opc == 7:
                nome = input("Nome: ")
                modelo = input("Modelo: ")
                categoria = input("Categoria: ")
                valor = float(input("Valor: "))
                quantidade_estoque = int(input("Quantidade de estoque: "))
                vlr_compra = float(input("Valor Compra: "))
                print(sisproduto.cadastrar_produto(nome, modelo, categoria, valor, quantidade_estoque, vlr_compra))
            elif opc == 8:
                id_produto = int(input("ID Produto: "))
                valor = float(input("Valor: "))
                print(sisproduto.editar_produto(id_produto, valor=valor))
            elif opc == 9:
                coluna = input("Coluna: ")
                dado = input("Dado: ")
                print(sisproduto.busca_produto(coluna, dado))
            elif opc == 0:
                print("Programa finalizado")
                break



        except Exception as e:
            print(f"Erro:  {e}")


if __name__ == "__main__":
    main()
