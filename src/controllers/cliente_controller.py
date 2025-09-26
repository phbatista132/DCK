import json
from src.controllers import Cliente

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
