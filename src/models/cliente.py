class Cliente:
    def __init__(self):
        self.cliente = {}

    def dados_cliente(self, id_cliente, nome, dt_nascimento, cpf, endereco, telefone, ativo):
        self.cliente = {
            'id_cliente' : id_cliente,
            'nome': nome,
            'dt_nascimento': dt_nascimento,
            'cpf': cpf,
            'endereco': endereco,
            'telefone': telefone,
            'status': ativo
        }
