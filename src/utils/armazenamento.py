class Item:
    def __init__(self, modelo, tipo, valor, codigo):
        self.produtos = []


    def cadastrar_produto(self):
         modelo = str(input()).strip().lower()
         tipo = str(input()).strip().lower()
         valor = float(input().replace('.',','))
         codigo = int(input())




