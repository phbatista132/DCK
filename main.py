from src.controllers.produto_controller import ProdutoController
from src.controllers.venda_controller import VendaController


def main():
    sisproduto = ProdutoController()
    sisvendas = VendaController()
    while True:
        try:
            opc = int(input('Opção: '))
            if opc == 1:
                print(sisvendas.total_compra())

            elif opc == 2:
                id_produto = int(input('ID: '))
                coluna = str(input('Coluna: '))
                dado = input('dado para alteração: ')
                sisproduto.editar_produto(id_produto, coluna, dado)

            elif opc == 3:
                id_produto = int(input("ID Produto"))
                print(sisproduto.desabilitar_produto(id_produto))

            elif opc == 4:
                produto = int(input('ID Produto: '))
                quantidade = int(input('Quantidade para venda: '))
                print(sisvendas.adicionar_item(produto, quantidade))

            elif opc == 5:
                cliente_id = int(input('Cliente: '))
                forma_pagamento = str(input('Forma de pagamento: '))
                print(sisvendas.finalizar_venda(cliente_id, forma_pagamento))

            elif opc == 0:
                print('Saindo do programa!')
                break
            else:
                print('Opção não localizada')

        except Exception as e:
            print(f"Erro:  {e}")


if __name__ == "__main__":
    main()
