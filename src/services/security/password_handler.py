import bcrypt
from typing import Tuple


class PasswordHandler:
    """
    Gerenciador de senhas usando bcrypt

    bcrypt:
    - Salt automatico unico por senha
    - Computacionalmente custoso (proteção contra brute force)
    - irreversivel (não descriptografa)
    """
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera hash bcrypt da senha

        Args:
            password: Senha em texto plano

        Returns:
            Hash bcrypt como string (já inclui o salt)
        """
        salt =bcrypt.gensalt()
        password = bcrypt.hashpw(password.encode(), salt)
        return password.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verifica se senha corresponde ao hash

        Args:
            password: Senha em texto plano
            hashed_password: Hash bcrypt armazenado

        Returns:
            True se senha correta, False caso contrário
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

        except Exception:
            return False

    @staticmethod
    def validar_forca_senha(password: str) -> Tuple[bool, str]:
        """
        Valida força da senha

        Requisitos:
        - Mínimo 8 caracteres
        - Pelo menos 1 letra maiúscula
        - Pelo menos 1 letra minúscula
        - Pelo menos 1 número
        - Pelo menos 1 caractere especial:
        """
        if len(password) < 8:
            return False, "Senha deve ter no minimo 8 caracteres"
        if not any(c.isupper() for c in password):
            return False, "Senha deve conter pelo menos 1 letra maiuscula"
        if not any(c.islower() for c in password):
            return False, "Senha deve conter pelo menos 1 letra minuscula"
        if not any(c.isdigit() for c in password):
            return False, "Senha deve conter pelo menos 1 número"

        especiais = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in especiais for c in password):
            return False, "Senha deve conter pelo menos 1 caractere especial"

        return True, "Senha forte"


