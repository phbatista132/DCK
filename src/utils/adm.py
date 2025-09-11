import json
from datetime import datetime
from cryptography.fernet import InvalidToken



def verifica_cli(cpf, caminho_arq, fernet):
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


class SistemaAdm:
    def __init__(self, fernet, descriptografar):
        self.fernet = fernet
        self.descriptografar = descriptografar

    def cadastrar_cliente(self, caminho_json="C:/Users/phbat/OneDrive/Desktop/DCK/src/clientes.json"):
        dados = Cliente.dados()
        if dados:
            nome, dt_nascimento, endereco, cpf = dados
            cliente = Cliente(nome, dt_nascimento, endereco, cpf, self.fernet, caminho_json)
            if cliente.dados:
                print("✅ Cliente cadastrado com sucesso.")
                return True
            else:
                print("⚠️ Cliente já existe na base.")
                return False
        else:
            print("⚠️ Dados inválidos ou incompletos.")
            return False

    def excluir_cliente(self, cpf, caminho_json="C:/Users/phbat/OneDrive/Desktop/DCK/src/clientes.json"):
        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                clientes = json.load(f)
        except (FileNotFoundError, json.JSONDecoder):
            print("Base não localizada")
        novos_clientes = []
        encontrado = False

        for cliente in clientes:
            cpf_salvo = self.descriptografar(cliente["cpf"], self.fernet)
            if cpf_salvo == cpf:
                encontrado = True
                continue
            novos_clientes.append(cliente)

        try:
            if encontrado:
                with open(caminho_json, "w", encoding="utf-8") as f:
                    json.dump(novos_clientes, f, indent=4, ensure_ascii=False)
                print("Cliente excluído com sucesso.")
                return True
            else:
                print("CPF não encontrado.")
                return False
        except Exception as e:
            print(f"Erro ao salvar os dados: {e} ")
























