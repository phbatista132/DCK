from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database import Clientes
from src.utils import validar_cpf, maior_idade
from src.utils.logKit import get_logger


class ClienteController:
    def __init__(self):
        self.cliente_log = get_logger("LoggerClienteController", "DEBUG")

    def cadastrar_cliente(self, db: Session, cpf: str, nome: str, dt_nascimento: str, telefone: str,
                          endereco: str) -> str:
        """ Cadastra novo cliente"""

        try:
            if not validar_cpf(cpf):
                self.cliente_log.warning("CPF inserido é invalido")
                return "CPF incorreto ou invalido"

            if not maior_idade(dt_nascimento):
                self.cliente_log.warning("Cliente menor idade")
                return "Cliente menor idade"

            dt_nascimento_obj = datetime.strptime(dt_nascimento, '%d/%m/%Y').date()

            cliente = Clientes(
                nome=nome,
                cpf=''.join(filter(str.isdigit, cpf)),
                dt_nascimento=dt_nascimento_obj,
                telefone=telefone,
                endereco=endereco
            )
            db.add(cliente)
            db.commit()
            db.refresh(cliente)

            self.cliente_log.info(f"Cliente: {nome} cadastrado (ID: {cliente.id_cliente})")
            return "Cliente Cadastrado com sucesso"

        except IntegrityError:
            db.rollback()
            self.cliente_log.warning("Cliente já cadastrado")
            return "Cliente já cadastrado"

        except Exception:
            db.rollback()
            self.cliente_log.exception(f"Erro ao cadastrar cliente: {nome}")
            return "Erro interno ao cadastrar cliente"

    def buscar_cliente(self, db: Session, cpf: str) -> Optional[Clientes]:
        """Buscar cliente por CPF"""

        try:
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            cliente = db.query(Clientes).filter(Clientes.cpf == cpf_limpo).first()

            if cliente:
                self.cliente_log.info(f"Cliente: {cliente.nome} localizado")

            return cliente
        except Exception:
            self.cliente_log.exception("Erro ao buscar cliente")
            return None

    def editar_cadastro(self, db: Session, cpf: str, **kwargs) -> str:
        """Edita dados de contato do cliente"""

        try:

            alteracoes_permitidas = ["telefone", "endereco"]

            for k in kwargs.keys():
                if k not in alteracoes_permitidas:
                    self.cliente_log.warning(f"Campo: {k} não permitido para alteração")
                    return "Dado não permitido para alteração"

            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            cliente = db.query(Clientes).filter(Clientes.cpf == cpf_limpo).first()

            if not cliente:
                self.cliente_log.warning(f"Cliente não encontrado")
                return "Cliente não encontrado"

            for key, value in kwargs.items():
                setattr(cliente, key, value)

            db.commit()
            self.cliente_log.info("Dados alterados com sucesso")
            return "Dados alterados com sucesso"

        except Exception:
            db.rollback()
            self.cliente_log.exception(f"Erro ao editar cadastro")
            return "Erro interno ao editar cadastro"

    def desativar_cliente(self, db: Session, cpf: str) -> str:
        """Realiza soft delete do cliente"""
        try:
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            cliente = db.query(Clientes).filter(Clientes.cpf == cpf_limpo).first()

            if not cliente:
                return "Cliente não encontrado"

            cliente.ativo = False
            db.commit()

            self.cliente_log.info("Cliente desativado com sucesso")
            return "Cliente desativado com sucesso"
        except Exception:
            db.rollback()
            self.cliente_log.exception("Erro ao desativar cliente")
            return "Erro interno ao desativar cliente"

    def listar_clientes(self, db: Session):
        """Listar todos os cliente ativos"""

        try:
            cliente = db.query(Clientes).filter(Clientes.ativo == True).all()

            if not cliente:
                return  "Sem clientes cadastrados"

            return cliente
        except Exception:
            self.cliente_log.exception("Erro ao listar clientes")
            return "Erro interno ao listar clientes"