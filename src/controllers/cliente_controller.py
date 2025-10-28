import json
from src.models.cliente import Cliente
from src.config import CLIENTES_DIR
from src.utils.file_helpers import gerar_arquivo, duplicado, verificar_arquivo_vazio
from src.utils.logKit.config_logging import get_logger
from src.utils.validators import validar_cpf, maior_idade


class ClienteController:
    def __init__(self):
        self.cliente_data = CLIENTES_DIR
        self.cliente_model = Cliente()
        self.cliente_log = get_logger("loggerClienteController", "DEBUG")

    def gera_id_cliente(self):
        if verificar_arquivo_vazio(self.cliente_data):
            return 1
        try:
            with open(self.cliente_data, "r", encoding='utf-8') as f:

                last_line = None
                for line in f:
                    if line.strip():
                        last_line = line

                if last_line:
                    ultimo_cliente = json.loads(last_line)
                    return ultimo_cliente.get('id_cliente', 0) + 1

                return 1
        except (json.JSONDecodeError, ValueError):
            return 1

    def cadastrar_cliente(self, nome: str, dt_nascimento: str, cpf: str, endereco: str, telefone: str):
        try:
            gerar_arquivo(self.cliente_data)
            self.cliente_log.debug(f"Cadastrando cliente {nome}")
            if not validar_cpf(cpf):
                self.cliente_log.warning("CPF inserido e invalido")
                return "CPF incorreto ou invalido"

            if not maior_idade(dt_nascimento):
                self.cliente_log.warning(f"Cliente menor de idade {nome}")
                return "Cliente menor de idade"

            if duplicado(self.cliente_data, cpf=cpf):
                self.cliente_log.warning("Cliente ja cadastrado")
                return "Cliente ja cadastrado"

            id_cliente = self.gera_id_cliente()
            self.cliente_model.dados_cliente(id_cliente, nome, dt_nascimento, cpf, endereco, telefone, ativo=True)
            with open(self.cliente_data, 'a', encoding='utf-8') as f:
                f.write(json.dumps(self.cliente_model.cliente, ensure_ascii=False) + '\n')

            self.cliente_model.cliente.clear()
            self.cliente_log.info(f"Cliente: {nome} cadastrado (ID: {id_cliente})")
            return "Cliente cadastrado com sucesso"

        except Exception as e:
            self.cliente_log.exception(f"Erro ao cadastrar cliente: {nome}")
            return f"Erro : {e}"

    def buscar_cliente(self, cpf: str) -> dict | str:
        try:
            self.cliente_log.debug(f"Buscando cliente {cpf}")

            if verificar_arquivo_vazio(self.cliente_data):
                self.cliente_log.warning("Arquivo vazio")
                return "Sem clientes cadastrados"

            with open(self.cliente_data, "r", encoding='utf-8') as f:
                clientes = [json.loads(line) for line in f if line.strip()]
                busca = next((c for c in clientes if c['cpf'] == cpf), None)

                if busca is None:
                    self.cliente_log.warning(f"Cliente não encontrado")
                    return f"Cliente não encontrado"

            self.cliente_log.info("Busca para o CPF concluida")
            return busca

        except Exception as e:
            self.cliente_log.exception(f"Erro ao buscar cliente")
            return f"Erro: {e}"

    def editar_cadastro(self, cpf, **kwargs) -> str:
        try:
            self.cliente_log.debug(f"Editando cliente {cpf}")

            alteracoes_permitidas = ["telefone", "endereco"]

            for k, v in kwargs.items():
                if k not in alteracoes_permitidas:
                    self.cliente_log.warning(f"Dado: {k} não permitodo para alteração")
                    return "Dado não pemitido para alteração"

            with open(self.cliente_data, "r", encoding='utf-8') as f:
                clientes = [json.loads(linhas) for linhas in f if linhas.strip()]

            encontrado = False
            for cliente in clientes:
                if cliente['cpf'] == cpf:
                    encontrado = True
                    cliente.update(kwargs)
                    break

            if not encontrado:
                return "Cliente não encontrado"

            with open(self.cliente_data, "w", encoding='utf-8') as f:
                for cliente in clientes:
                    f.write(json.dumps(cliente, ensure_ascii=False) + '\n')
            self.cliente_log.info(f"Dados alterados com sucesso")
            return "Dados alterados com sucesso"
        except Exception as e:
            self.cliente_log.exception(f"Erro ao editar cliente")
            return f"Erro: {e}"

    def desativar_cliente(self, cpf) -> str:
        try:
            self.cliente_log.debug(f"Desativando cliente {cpf}")
            if verificar_arquivo_vazio(self.cliente_data):
                self.cliente_log.warning("Arquivo vazio")
                return "Sem clientes cadastrados"

            with open(self.cliente_data, "r", encoding='utf-8') as f:
                clientes = [json.loads(cliente) for cliente in f if cliente.strip()]

            encontrado = False
            for cliente in clientes:
                if cliente['cpf'] == cpf:
                    cliente['ativo'] = False
                    encontrado = True
                    break

            if not encontrado:
                return "Cliente não encontrado"

            with open(self.cliente_data, "w", encoding='utf-8') as f:
                for cliente in clientes:
                    f.write(json.dumps(cliente, ensure_ascii=False) + '\n')

            self.cliente_log.info(f"Cliente desativado com sucesso")
            return "Cliente desativado"

        except Exception as e:
            self.cliente_log.exception(f"Erro ao desativar cliente")
            return f"Erro: {e}"

    def listar_clientes(self):
        try:
            self.cliente_log.debug(f"Listando clientes")
            if verificar_arquivo_vazio(self.cliente_data):
                self.cliente_log.warning("Arquivo vazio")
                return "Sem clientes cadastrados"

            cliente_ativos = []
            with open(self.cliente_data, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        cliente = json.loads(line)
                        if cliente.get('ativo'):
                            cliente_ativos.append(cliente)

            return cliente_ativos

        except Exception as e:
            self.cliente_log.exception(f"Erro ao listar clientes")
            return f"Erro: {e}"
