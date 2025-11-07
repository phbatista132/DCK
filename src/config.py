from os import getenv
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(".env")

ROOT_DIR = Path(".").resolve()
DATA_DIR = ROOT_DIR / "data"

PRODUTOS_DATA =Path(DATA_DIR/getenv("PRODUTOS_FILE","estoque.csv"))
VENDAS_DIR =Path(DATA_DIR/getenv('VENDAS_FILE',"vendas.csv"))
ITENS_VENDAS_DIR =Path(DATA_DIR/getenv('ITENS_VENDAS_FILE',"itens_vendas.csv"))
CLIENTES_DIR = Path(DATA_DIR / getenv("CLIENTES_FILE", "clientes.jsonl"))
