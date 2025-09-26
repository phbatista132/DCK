import json
from cryptography.fernet import InvalidToken


def verifica_cli(cpf, fernet, caminho_arq="C:/Users/phbat/OneDrive/Desktop/DCK/src/clientes.json"):
    try:
        with open(caminho_arq, 'r', encoding='utf-8') as f:
            clientes = json.load(f)
    except FileNotFoundError:
        return False

    for cliente in clientes:
        try:
            cpf_salvo = fernet.decrypt(cliente['cpf'].encode()).decode()
            if cpf_salvo == cpf:
                return True
        except InvalidToken:
            continue
    return False

def salvar_cadastro(dados, caminho_arq):
    try:
        with open(caminho_arq, 'r', encoding='utf-8') as f:
            novo_cadastro = json.load(f)
    except FileNotFoundError:
        novo_cadastro = []

    novo_cadastro.append(dados)

    with open(caminho_arq, 'w', encoding='utf-8') as f:
        json.dump(novo_cadastro, f, ensure_ascii=False, indent=4)



class Cliente:

    def __init__(self, nome, dt_nascimento, endereco, cpf, fernet, caminho_json="C:/Users/phbat/OneDrive/Desktop/DCK/src/clientes.json"):
        self.clientes = caminho_json


        if verifica_cli(cpf, self.clientes, fernet):
            print("Cliente ja cadastrado")
            self.dados = None
        else:
            self.cadastro ={
                'nome': nome,
                'dt_nascimento':dt_nascimento,
                'endereco':endereco,
                'cpf': fernet.encrypt(cpf.encode()).decode()
            }
            salvar_cadastro(self.cadastro, self.clientes)


    @staticmethod
    def dados():
        nome = str(input("Nome: "))
        dt_nascimento = str(input("Data de nascimento: "))
        endereco = str(input("Endereco: "))
        cpf = input("CPF: ").replace('.', '').replace('-', '')
        return nome, dt_nascimento, endereco, cpf