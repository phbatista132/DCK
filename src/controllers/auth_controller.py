from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.models import Usuarios
from src.services.security.password_handler import PasswordHandler
from src.services.security.jwt_handler import JWTHandler

from src.utils.validators import validar_cpf
from src.utils.logKit.config_logging import get_logger


class AuthController:
    """Controller para autenticação e gerenciamento de usuários"""

    def __init__(self):
        self.auth_log = get_logger("LoggerAuthController", "INFO")
        self.password_handler = PasswordHandler()

    def registrar_usuario(self, db: Session, username: str, email: str, senha: str, nome_completo: str,
                          tipo_usuario: str = "cliente", cpf: Optional[str] = None) -> Tuple[bool, str, Optional[dict]]:
        """
        Registra novo usuário no sistema

        Args:
            db: Sessão do banco de dados
            username: Nome de usuário único
            email: Email único e válido
            senha: Senha em texto plano (será hasheada)
            nome_completo: Nome completo
            tipo_usuario: admin, gerente, vendedor, cliente
        """
        try:
            # Validações básicas
            if len(username) < 3:
                return False, "Username deve ter no mínimo 3 caracteres", None

            if '@' not in email or '.' not in email:
                return False, "Email inválido", None

            # Validar força da senha
            senha_valida, msg_senha = self.password_handler.validar_forca_senha(senha)
            if not senha_valida:
                return False, msg_senha, None

            if tipo_usuario not in ['admin', 'gerente', 'vendedor', 'cliente']:
                return False, "Tipo de usuário inválido", None

            # Validar CPF se fornecido
            if cpf and not validar_cpf(cpf):
                return False, "CPF inválido", None

            # Hash da senha
            senha_hash = self.password_handler.hash_password(senha)

            # Criptografar dados sensíveis

            # Criar usuário
            usuario = Usuarios(
                username=username.lower(),
                email=email.lower(),
                senha_hash=senha_hash,
                nome_completo=nome_completo,
                tipo_usuario=tipo_usuario,

            )

            db.add(usuario)
            db.commit()
            db.refresh(usuario)

            self.auth_log.info(
                f"Usuário registrado: {username} (ID: {usuario.id_usuario}, Tipo: {tipo_usuario})"
            )

            # Retornar dados seguros
            usuario_dict = {
                'id_usuario': usuario.id_usuario,
                'username': usuario.username,
                'email': usuario.email,
                'nome_completo': usuario.nome_completo,
                'tipo_usuario': usuario.tipo_usuario,
                'ativo': usuario.ativo,
                'data_cadastro': usuario.data_cadastro.isoformat()
            }

            return True, "Usuário registrado com sucesso", usuario_dict

        except IntegrityError as ie:
            db.rollback()
            if 'username' in str(ie):
                self.auth_log.warning(f"Username duplicado: {username}")
                return False, "Username já está em uso", None
            elif 'email' in str(ie):
                self.auth_log.warning(f"Email duplicado: {email}")
                return False, "Email já está cadastrado", None
            else:
                self.auth_log.exception("Erro de integridade ao registrar usuário")
                return False, "Erro ao registrar usuário", None

        except Exception as e:
            db.rollback()
            self.auth_log.exception(f"Erro ao registrar usuário: {username}")
            return False, "Erro interno ao registrar usuário", None

    def login(self, db: Session, username: str, senha: str) -> Tuple[bool, str, Optional[dict]]:
        """Autentica usuário e gera tokens JWT"""
        try:
            # Buscar usuário
            usuario = db.query(Usuarios).filter(
                Usuarios.username == username.lower()
            ).first()

            if not usuario:
                self.auth_log.warning(f"Tentativa de login com username inexistente: {username}")
                return False, "Credenciais inválidas", None

            # Verificar se está ativo
            if not usuario.ativo:
                self.auth_log.warning(f"Tentativa de login de usuário inativo: {username}")
                return False, "Usuário desativado", None

            # Verificar senha
            if not self.password_handler.verify_password(senha, usuario.senha_hash):
                self.auth_log.warning(f"Tentativa de login com senha incorreta: {username}")
                return False, "Credenciais inválidas", None

            # Atualizar último acesso
            usuario.ultimo_acesso = datetime.utcnow()
            db.commit()

            # Gerar tokens
            token_data = {
                "user_id": usuario.id_usuario,
                "username": usuario.username,
                "tipo_usuario": usuario.tipo_usuario
            }

            access_token = JWTHandler.create_access_token(token_data)
            refresh_token = JWTHandler.create_refresh_token(token_data)

            self.auth_log.info(f"Login bem-sucedido: {username}")

            return True, "Login realizado com sucesso", {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    'id_usuario': usuario.id_usuario,
                    'username': usuario.username,
                    'email': usuario.email,
                    'nome_completo': usuario.nome_completo,
                    'tipo_usuario': usuario.tipo_usuario,
                    'ativo': usuario.ativo
                }
            }

        except Exception as e:
            self.auth_log.exception(f"Erro ao realizar login: {username}")
            return False, "Erro interno ao fazer login", None

    def buscar_usuario(self,db: Session,user_id: int = None, username: str = None, email: str = None) -> Optional[Usuarios]:
        """Busca usuário por ID, username ou email"""
        try:
            query = db.query(Usuarios)

            if user_id:
                return query.filter(Usuarios.id_usuario == user_id).first()
            elif username:
                return query.filter(Usuarios.username == username.lower()).first()
            elif email:
                return query.filter(Usuarios.email == email.lower()).first()

            return None

        except Exception as e:
            self.auth_log.exception("Erro ao buscar usuário")
            return None

    def alterar_senha(
            self,
            db: Session,
            user_id: int,
            senha_atual: str,
            nova_senha: str
    ) -> Tuple[bool, str]:
        """Permite usuário alterar própria senha"""
        try:
            # Validar nova senha
            senha_valida, msg_senha = self.password_handler.validar_forca_senha(nova_senha)
            if not senha_valida:
                return False, msg_senha

            usuario = self.buscar_usuario(db, user_id=user_id)

            if not usuario:
                return False, "Usuário não encontrado"

            # Verificar senha atual
            if not self.password_handler.verify_password(senha_atual, usuario.senha_hash):
                self.auth_log.warning(
                    f"Tentativa de alteração de senha com senha atual incorreta: user_id={user_id}"
                )
                return False, "Senha atual incorreta"

            # Atualizar senha
            usuario.senha_hash = self.password_handler.hash_password(nova_senha)
            db.commit()

            self.auth_log.info(f"Senha alterada com sucesso: user_id={user_id}")
            return True, "Senha alterada com sucesso"

        except Exception as e:
            db.rollback()
            self.auth_log.exception(f"Erro ao alterar senha: user_id={user_id}")
            return False, "Erro ao alterar senha"

    def desativar_usuario(self, db: Session, user_id: int) -> Tuple[bool, str]:
        """Desativa usuário (soft delete)"""
        try:
            usuario = self.buscar_usuario(db, user_id=user_id)

            if not usuario:
                return False, "Usuário não encontrado"

            usuario.ativo = False
            db.commit()

            self.auth_log.info(f"Usuário desativado: user_id={user_id}")
            return True, "Usuário desativado com sucesso"

        except Exception as e:
            db.rollback()
            self.auth_log.exception(f"Erro ao desativar usuário: user_id={user_id}")
            return False, "Erro ao desativar usuário"

    def listar_usuarios(
            self,
            db: Session,
            tipo_usuario: Optional[str] = None,
            incluir_inativos: bool = False
    ) -> list:
        """Lista usuários (opcionalmente filtrados por tipo)"""
        try:
            query = db.query(Usuarios)

            # Filtrar por status ativo
            if not incluir_inativos:
                query = query.filter(Usuarios.ativo == True)

            # Filtrar por tipo
            if tipo_usuario:
                query = query.filter(Usuarios.tipo_usuario == tipo_usuario)

            usuarios = query.all()

            # Converter para dict removendo dados sensíveis
            return [
                {
                    'id_usuario': u.id_usuario,
                    'username': u.username,
                    'email': u.email,
                    'nome_completo': u.nome_completo,
                    'tipo_usuario': u.tipo_usuario,
                    'ativo': u.ativo,
                    'data_cadastro': u.data_cadastro.isoformat(),
                    'ultimo_acesso': u.ultimo_acesso.isoformat() if u.ultimo_acesso else None
                }
                for u in usuarios
            ]

        except Exception as e:
            self.auth_log.exception("Erro ao listar usuários")
            return []
