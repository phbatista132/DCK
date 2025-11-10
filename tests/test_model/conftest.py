import pytest
from datetime import date, datetime


@pytest.fixture
def data_valida():
    """Data válida para testes"""
    return date(2025, 1, 15)


@pytest.fixture
def data_nascimento_maior_idade():
    """Data de nascimento de pessoa maior de idade"""
    return date(1990, 5, 20)


@pytest.fixture
def data_nascimento_menor_idade():
    """Data de nascimento de pessoa menor de idade"""
    return date(2010, 5, 20)


@pytest.fixture
def datetime_valida():
    """Datetime válida para testes"""
    return datetime(2025, 1, 15, 14, 30, 0)