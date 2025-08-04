class Produto:
    def __init__(self):
        self.produtos = []

    def cadastrar_produto(self):
        cadastro = dict()
        cadastro['modelo'] = str(input()).strip().lower()
        cadastro['tipo'] = str(input()).strip().lower()
        cadastro['valor']= float(input().replace(',','.'))
        cadastro['codigo'] = int(input())
        self.produtos.append(cadastro)
        return f'produto cadastrado'

    def deletar_produto(self):
        busca = str(input())
        for filtro in self.produtos:
            if busca in filtro['modelo']:
                self.produtos.remove(filtro)
            else:
                print("item não localizado")
        return f"O produto {busca} foi elimando com sucesso"

    def listar_produtos(self):
        for lista in self.produtos:
            print(lista)






def main():
    teste = Produto()
    while True:
        try:
            opc = int(input())
            if opc == 1:
                print(teste.cadastrar_produto())

            elif opc == 2:
                teste.listar_produtos()
            elif opc == 3:
                print(teste.deletar_produto())
            elif opc == 0:
                print("Saindo do programa!")
                break
        except ValueError:
            print("Digite o valor corretamente")


if __name__ == "__main__":
    main()









