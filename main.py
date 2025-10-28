from src.controllers.produto_controller import ProdutoController
from src.controllers.venda_controller import VendaController
from src.controllers.cliente_controller import ClienteController


def main():
    sisproduto = ProdutoController()
    sisvendas = VendaController()
    siscliente = ClienteController()
    while True:
        try:
            opc = int(input('Opção: '))
            if opc == 1:
               cpf=input("CPF: ")
               print(siscliente.excluir_cliente(cpf))

            elif opc == 2:
                nome = input("Nome: ")
                dt_nascimento = input("Data de nascimento: ")
                cpf = input("CPF: ")
                endereco = input("Endereço: ")
                telefone = input("Telefone: ")
                print(siscliente.cadastrar_cliente(nome, dt_nascimento, cpf, endereco, telefone))

            elif opc == 3:
                cpf = input("CPF: ")
                print(siscliente.buscar_cliente(cpf))

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
