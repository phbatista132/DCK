from pathlib import Path
import os

def gerar_arquivo(arquivo: Path) -> bool:
    if not arquivo.exists():
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.touch()
        return True
    return False

def verificar_aquivo_vazio(arquivo: Path):
    return not arquivo.exists() or os.path.getsize(arquivo) == 0