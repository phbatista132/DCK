from pathlib import Path
import os
import pandas as pd
import json
from src.config import PRODUTOS_DATA

def gerar_arquivo(arquivo: Path) -> bool:
    if not arquivo.exists():
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.touch()
        return True
    return False

def verificar_arquivo_vazio(arquivo: Path) -> bool:
    if not arquivo.exists():
        return True  # Arquivo não existe → considerado "vazio"
    return os.path.getsize(arquivo) == 0  # Retorna True se o tamanho for 0


def duplicado(arquivo, **kwargs) -> bool:
    extensao = os.path.splitext(arquivo)[1].lower()


    if extensao == '.csv':
        dados = pd.read_csv(arquivo, encoding='utf-8', sep=',').to_dict(orient='records')
    elif extensao == '.jsonl':
        if verificar_arquivo_vazio(arquivo):
            return False
        else:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = []
                for items in f:
                    item = json.loads(items)
                    dados.append(item)
    else:
        raise ValueError("Formato de arquivo não suportado")

    for item in dados:
        if all(str(item.get(k)) == str(v) for k, v in kwargs.items()):
            return True

    return False

