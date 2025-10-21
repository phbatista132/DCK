from os import getenv
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(".env")

ROOT_DIR = Path(".").resolve()
DATA_DIR = ROOT_DIR / "data"

PRODUTOS_DATA = DATA_DIR / getenv("PRODUTOS_FILE ","estoque.csv")
CLIENTES_DIR = DATA_DIR / getenv("CLIETNTES_FILE","clientes.json")
VENDAS_DIR = DATA_DIR / getenv('VENDAS_FILE',"vendas.csv")