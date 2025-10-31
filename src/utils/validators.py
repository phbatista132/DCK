import re
from datetime import datetime, date



def validar_cpf(cpf: str) -> bool:
    """
    Responsavel por verificar se o CPF digita é valido matematicamente.
    :param cpf: Cadastro de Pessoa Fisica brasileira, o parametrô aguarda um tipo string com 11 digitos numericos
    :return: Retorna True ou False
    """
    try:
        cpf = ''.join(filter(str.isdigit, cpf))

        if len(cpf) != 11:
            return False

        if cpf == cpf[0] * 11:
            return False

        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        dv1 = 0 if soma % 11 < 2 else 11 - (soma % 11)

        if int(cpf[9]) != dv1:
            return False

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        dv2 = 0 if soma % 11 < 2 else 11 - (soma % 11)

        return int(cpf[10]) == dv2

    except (ValueError, TypeError, IndexError):
        return False


def maior_idade(dt_nascimento: date) -> bool:
    """
    Verifica se a pessoa tem 18 anos ou mais

    Args
        dt_nascimento: String no formato DD/MM/YYYY

    Return:
        bool: True se for maior de idade
    """
    try:
        hoje = datetime.today()

        idade = hoje.year - dt_nascimento.year

        if (hoje.month, hoje.day) < (dt_nascimento.month, dt_nascimento.day):
            idade -= 1

        return idade >= 18

    except (ValueError, TypeError):
        return False


def validar_email(email: str) -> bool:
    padrao_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.fullmatch(padrao_email, email))


def validar_telefone(telefone: str) -> bool:
    ddds_validos = [
        11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38, 41, 42, 43, 44, 45, 46, 47,
        48, 49, 51, 53, 54, 55, 61, 62, 64, 65, 66, 67, 68, 69, 71, 73, 74, 75, 77, 79, 81, 87, 82, 83, 84, 85, 88, 86,
        89, 91, 93, 94, 92, 97, 95, 96, 98, 99, 63
    ]

    if not telefone or len(telefone) < 10:
        return False


    apenas_numeros = re.sub(r'\D', '', telefone)


    if len(apenas_numeros) not in [10, 11]:
        return False


    ddd = int(apenas_numeros[:2])
    if ddd not in ddds_validos:
        return False


    padrao_telefone = r"^\(?\d{2}\)?[-.\s]?\d{4,5}[-.\s]?\d{4}$"
    return bool(re.match(padrao_telefone, telefone))



