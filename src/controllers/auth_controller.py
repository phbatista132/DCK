import json
from datetime import datetime
from typing import Optional, Tuple
from src.models.usuario import Usuario
from src.services.security import JWTHandler, PasswordHandler
from src.utils import gerar_arquivo, verificar_arquivo_vazio, validar_email
from src.utils.logKit import get_logger
from src.config import USUARIOS_DIR


class AuthController:
    """Controller para autenticação e gerenciamento de usuarios"""

    def __init__(self):
        self.usuarios_data = USUARIOS_DIR
        self.auth_log = get_logger("LoggerAuthController", "INFO")
        self.password_handler = PasswordHandler()

    def _gerar_id_usuario(self) -> int:
        """Gerar ID único para novo usuario"""
        if verificar_arquivo_vazio(self.usuarios_data):
            return 1

        try:
            with open(self.usuarios_data, "r", encoding='utf-8') as f:
                last_line = None
                for line in f:
                    if line.strip():
                        last_line = line

                if last_line:
                    ultimo_user = json.loads(last_line)
                    return ultimo_user.get('id_usuario', 0) + 1

                return 1

        except (json.JSONDecodeError, ValueError):
            return 1

    def _usuario_existe(self, username: str = None, email: str = None) -> bool:
        """Verifica se um usuario já existe por username ou email"""

        if verificar_arquivo_vazio(self.usuarios_data):
            return False

        try:
            with open(self.usuarios_data, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        usuario = json.loads(line)
                        if username and usuario.get('username') == username:
                            return True
                        if email and usuario.get('email') == email:
                            return True

                return False
        except Exception as e:
            self.auth_log.exception("Erro ao verificar existencia de usuario")
            return False

    def registrar_usuario(self, username: str, email: str, senha: str, nome_completo: str, tipo_usuario: str,
                          ) -> Tuple[bool, str, Optional[str]]:
        """
        Registrar usuario

        Args:
            username: Usuario
            email: Email
            senha: Senha
            nome_completo: Nome completo
            tipo_usuario: admin, gerente, vendedor, cliente

        Returns:
            (sucesso: bool, mensagem: str, dados_usuario: str)
        """
        try:
            gerar_arquivo(self.usuarios_data)

            if len(username) < 3:
                return False, "Username deve ter no minimo 3 caracteres", None

            if not validar_email(email):
                return False, "Email Invalido", None

            senha_valida, msg_senha = self.password_handler.validar_forca_senha(senha)
            if not senha_valida:
                return False, msg_senha, None

            if tipo_usuario not in ['admin', 'gerente', 'vendedor', 'cliente']:
                return False, "Tipo de usuário inválido", None

            if self._usuario_existe(username=username):
                self.auth_log.warning(f"Tentativa de registro com username duplicado: {username}")
                return False, "Username já esta em uso", None

            if self._usuario_existe(email=email):
                self.auth_log.warning(f"Tentativa de registro com email duplicado: {email}")
                return False, "Email já está cadastrado", None

            senha_hash = self.password_handler.hash_password(senha)
            id_usuario = self._gerar_id_usuario()

            usuario = Usuario(
                id_usuario=id_usuario,
                username=username,
                email=email,
                senha_hash=senha_hash,
                nome_completo=nome_completo,
                tipo_usuario=tipo_usuario
            )

            with open(self.usuarios_data, "a", encoding='utf-8') as f:
                f.write(json.dumps(usuario.to_dict(), ensure_ascii=False, default=str))

            self.auth_log.info(f"Usuario registrado: {username} (ID: {id_usuario})")

            return True, "Usuario registrado com sucesso", None

        except Exception as e:
            self.auth_log.exception(f"Erro ao registrar usuario: {username}")
            return False, "Erro interno ao registrar usuario", None

    def login(self, username: str, senha: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Autentica usuario e gera tokens JWT

        Returns:
             (sucesso: bool, mensagem: str, tokens: dict)
             tokens ={
                "acess_token":"..."
                "refresh_token":"..."
                "token_type": "bearer"
                "user":{...}
             }
        """
        try:
            usuario = self._buscar_usuario(username=username)

            if not usuario:
                self.auth_log.warning(f"Tentativa de login com username inexistente: {username}")
                return False, "Credenciais invalidos", None

            if not usuario.get('ativo'):
                self.auth_log.warning(f"tentativa de login com ativo: {username}")
                return False, "Usuario desativado", None

            if not self.password_handler.verify_password(senha, usuario["senha_hash"]):
                self.auth_log.warning(f"tentativa de login com senha incorreta: {username}")
                return False, "Credenciais invalidas", None

            self._atualizar_ultimo_acesso(usuario["id_usuario"])

            token_data = {
                "user_id": usuario["id_usuario"],
                "username": usuario["username"],
                "tipo_usuario": usuario["tipo_usuario"]
            }

            access_token = JWTHandler.create_access_token(token_data)
            refresh_token = JWTHandler.create_refresh_token(token_data)

            self.auth_log.info(f"Login bem-sucedido: {username}")

            usuario_safe = {k: v for k, v in usuario.items() if k not in ['senha_hash']}

            return True, "Login realizado com sucesso", {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": usuario_safe
            }
        except Exception as e:
            self.auth_log.exception(f"Erro ao realizar login: {username}")
            return False, "Erro interno ao fazer login", None

    def _buscar_usuario(self, user_id: int = None, username: str = None, email: str = None) -> Optional[dict]:
        """Buscar usuario por ID, username e email"""
        if verificar_arquivo_vazio(self.usuarios_data):
            return None

        try:
            with open(self.usuarios_data, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        usuario = json.loads(line)
                        if user_id and usuario.get('id_usuario') == user_id:
                            return usuario
                        if username and usuario.get('username') == username:
                            return usuario
                        if email and usuario.get('email') == email:
                            return usuario
                return None
        except Exception as e:
            self.auth_log.exception(f"Erro ao buscar usuario: {username}")
            return None


    def _atualizar_ultimo_acesso(self, user_id: int) -> None:
        """Atualizar timestamp do ultimo acesso"""
        try:
            with open(self.usuarios_data, "r", encoding='utf-8') as f:
                usuarios = [json.loads(line) for line in f if line.strip()]

            for usuario in usuarios:
                if usuario['id_usuario'] == user_id:
                    usuario['ultimo_acesso'] = datetime.now().isoformat()
                    break
            with open(self.usuarios_data, "w", encoding='utf-8') as f:
                for usuario in usuarios:
                    f.write(json.dumps(usuario, ensure_ascii=False, default=str) + '\n')

        except Exception as e:
            self.auth_log.exception(f"Erro ao atualizar ultimo acesso do usuario: {user_id}")

    def refresh_token(self, refres_token: str) -> Tuple[bool, str, Optional[dict]]:
        """Gera novo token usando refresh token"""

        try:
            payload = JWTHandler.verify_token(refres_token, token_type="refresh")

            if not payload:
                return False, "Refresh token invalido ou expirado", None

            usuario = self._buscar_usuario(user_id=payload["id_usuario"])

            if not usuario or not usuario.get("ativo"):
                return False, "Usuario invalido ou desativado", None

            token_data = {
                "user_id": payload["id_usuario"],
                "username": payload["username"],
                "tipo_usuario": payload["tipo_usuario"]
            }

            new_access_token = JWTHandler.create_refresh_token(token_data)

            return True, "Token renovado", {
                "access_token": new_access_token,
                "token_type": "bearer"
            }
        except Exception as e:
            self.auth_log.exception("Erro ao renovar token")
            return False, "Erro ao renovar token", None

    def alterar_senha(self, user_id: int, senha_atual: str, nova_senha: str) -> Tuple[bool, str]:
        """Permite usuário alterar própria senha"""
        try:
            # Validar nova senha
            senha_valida, msg_senha = self.password_handler.validar_forca_senha(nova_senha)
            if not senha_valida:
                return False, msg_senha

            usuario = self._buscar_usuario(user_id=user_id)

            if not usuario:
                return False, "Usuário não encontrado"

            # Verificar senha atual com bcrypt
            if not self.password_handler.verify_password(senha_atual, usuario['senha_hash']):
                self.auth_log.warning(f"Tentativa de alteração de senha com senha atual incorreta: user_id={user_id}")
                return False, "Senha atual incorreta"

            # Gerar hash da nova senha
            novo_hash = self.password_handler.hash_password(nova_senha)

            # Atualizar
            usuarios = []
            with open(self.usuarios_data, 'r', encoding='utf-8') as f:
                usuarios = [json.loads(line) for line in f if line.strip()]

            for u in usuarios:
                if u['id_usuario'] == user_id:
                    u['senha_hash'] = novo_hash
                    break

            with open(self.usuarios_data, 'w', encoding='utf-8') as f:
                for u in usuarios:
                    f.write(json.dumps(u, ensure_ascii=False, default=str) + '\n')

            self.auth_log.info(f"Senha alterada com sucesso: user_id={user_id}")
            return True, "Senha alterada com sucesso"

        except Exception as e:
            self.auth_log.exception(f"Erro ao alterar senha: user_id={user_id}")
            return False, "Erro ao alterar senha"

    def desativar_usuario(self, user_id: int) -> Tuple[bool, str]:
        """Desativa usuário (soft delete)"""
        try:
            usuarios = []
            with open(self.usuarios_data, 'r', encoding='utf-8') as f:
                usuarios = [json.loads(line) for line in f if line.strip()]

            encontrado = False
            for usuario in usuarios:
                if usuario['id_usuario'] == user_id:
                    usuario['ativo'] = False
                    encontrado = True
                    break

            if not encontrado:
                return False, "Usuário não encontrado"

            with open(self.usuarios_data, 'w', encoding='utf-8') as f:
                for usuario in usuarios:
                    f.write(json.dumps(usuario, ensure_ascii=False, default=str) + '\n')

            self.auth_log.info(f"Usuário desativado: user_id={user_id}")
            return True, "Usuário desativado com sucesso"

        except Exception as e:
            self.auth_log.exception(f"Erro ao desativar usuário: user_id={user_id}")
            return False, "Erro ao desativar usuário"

    def listar_usuarios(self, tipo_usuario: Optional[str] = None, incluir_inativos: bool = False) -> list:
        """Lista usuários (opcionalmente filtrados por tipo)"""
        try:
            if verificar_arquivo_vazio(self.usuarios_data):
                return []

            usuarios = []
            with open(self.usuarios_data, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        usuario = json.loads(line)

                        # Filtrar por status ativo
                        if not incluir_inativos and not usuario.get('ativo'):
                            continue

                        # Filtrar por tipo
                        if tipo_usuario and usuario.get('tipo_usuario') != tipo_usuario:
                            continue

                        # Remover dados sensíveis
                        usuario_safe = {k: v for k, v in usuario.items()
                                        if k not in ['senha_hash', 'cpf_criptografado', 'telefone_criptografado']}
                        usuarios.append(usuario_safe)

            return usuarios

        except Exception as e:
            self.auth_log.exception("Erro ao listar usuários")
            return []