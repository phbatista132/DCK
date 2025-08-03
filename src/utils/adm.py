class Cliente:
    def __init__(self, nome, dt_nasc, cpf):
        self.nome = nome
        self.dt_nasc = dt_nasc
        self.__cpf = cpf
        self.compras = []

    def realiza_compra(self, item, valor):
        itens = {'item': item,'valor': valor}
        self.compras.append(itens)

        return self.compras




