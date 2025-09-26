from src.controllers.produto_controller import ProdutoController


def main():
    sisproduto = ProdutoController()

    try:
        opc = int(input('Opção: '))
        if opc == 1:
            nome = str(input('Nome: '))
            modelo = str(input('Modelo: '))
            categoria = str(input('categoria: '))
            valor = float(input("Valor: ").replace(',', '.'))
            quantidade = int(input('Quantidade: '))
            vl_compra = float(input('Valor compra: ').replace(',', '.'))
            sisproduto.cadastrar_produto(nome, modelo, categoria, valor , quantidade, vl_compra)
        elif opc == 2:
            id_produto = int(input('ID: '))
            coluna = str(input('Coluna: '))
            dado = input('dado para alteração: ')
            sisproduto.editar_produto(id_produto, coluna, dado)

        elif opc == 3:
            coluna =  str(input('Filtra por: '))
            dado_busca = input('Produto: ')
            sisproduto.busca_produto(coluna, dado_busca)
        else:
            print('Opção não localizada')
    except Exception as e:
        print(f"Erro:  {e}")


if __name__ == '__main__':
    main()
