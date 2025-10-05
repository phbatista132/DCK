class Produto:
    def __init__(self):
        self.produtos = []

    def dados(self, nome, modelo, categoria, valor, codigo, estoque, dt_cadastro, vlr_compra, margem_lucro):
        self.produtos.append({
            'nome': nome,
            'modelo': modelo,
            'categoria': categoria,
            'valor': valor,
            'codigo': codigo,
            'quantidade_estoque': estoque,
            'data_cadastro': dt_cadastro,
            'vlr_compra': vlr_compra,
            'margem_lucro': margem_lucro
        })

    @staticmethod
    def valor_positivo(valor: float) -> bool:
        if valor >= 0:

            return True
        else:

            return False

    @staticmethod
    def margem_lucro(valor_venda, valor_compra):
        if valor_venda == 0:
            return 0

        margem = ((valor_venda - valor_compra) / valor_compra) * 100

        return round(margem, 2)

    @staticmethod
    def formato(row):
        return f'Produto: {row['nome']} | Modelo: {row['modelo']} | Categoria: {row['categoria']}| Valor:  {row['valor']} | Quantidade: {row['quantidade_estoque']}'

    def validar_dados(self, valor, valor_compra, quantidade_estoque) -> bool:

        if not self.valor_positivo(valor):
            return False
        if not self.valor_positivo(valor_compra):
            return False
        if not self.valor_positivo(quantidade_estoque):
            return False

        return True
