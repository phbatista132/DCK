from cryptography.fernet import Fernet, InvalidToken
import os
def carregar_fernet(caminho="C:/Users/phbat/OneDrive/Desktop/DCK/src/security/chave.key"):
    if not os.path.exists(caminho):
        chave = Fernet.generate_key()
        with open(caminho, "wb") as f:
            f.write(chave)
    else:
        with open(caminho, "rb") as f:
            chave = f.read()
    return Fernet(chave)


def descriptografar(dado_cripto: str, fernet: Fernet) -> str | None:
    try:
        return fernet.decrypt(dado_cripto.encode()).decode()
    except InvalidToken:
        return None

def criptografar(dado: str, fernet: Fernet) -> str | None:
    try:
        return fernet.encrypt(dado.encode()).decode()
    except Exception as e:
        print(f'Erro: {e}')
        return None



