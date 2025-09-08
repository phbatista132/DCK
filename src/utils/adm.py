import json
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken

chave = Fernet.generate_key()
fernet = Fernet(chave)

def verifica_cli(cpf, caminho_arq, fernet):
    try:
        with open(caminho_arq, 'r', encoding='utf-8') as f:
            clientes = json.load(f)
    except FileNotFoundError:
        return False

    for cliente in clientes:
        try:
            cpf_savlo = fernet.decrypt(cliente['cpf'].enconde()).decode()
            if cpf_savlo == cpf:
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

    def __init__(self, nome, dt_nascimento, endereco, cpf, fernet, caminhojson='clientes.json'):
        self.clientes = caminhojson

        if verifica_cli(cpf, self.clientes, fernet):
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


class SistemaAdm:
    def __init__(self):
        self.cliente = Cliente
    @staticmethod
    def cadastrar_cliente(fernet, caminho_json="clientes.json"):
        dados = Cliente.dados()
        if dados:
            nome, dt_nascimento, endereco, cpf = dados
            Cliente(nome, dt_nascimento, endereco, cpf, fernet, caminho_json)












