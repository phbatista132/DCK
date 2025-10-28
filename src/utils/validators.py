from datetime import datetime

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

def maior_idade(dt_nascimento: str) -> bool:
    """
    Verifica se a pessoa tem 18 anos ou mais

    Args
        dt_nascimento: String no formato DD/MM/YYYY

    Return:
        bool: True se for maior de idade
    """
    try:

        data_nasc = datetime.strptime(dt_nascimento, '%d/%m/%Y')
        hoje = datetime.today()

        idade = hoje.year - data_nasc.year

        if (hoje.month, hoje.day) < (data_nasc.month, data_nasc.day):
            idade -= 1

        return idade >= 18

    except (ValueError, TypeError):
        return False
