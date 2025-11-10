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
USUARIOS_DIR = Path(DATA_DIR / getenv("USUARIOS_FILE", "usuarios.jsonl"))
JWT_SECRET_KEY = getenv("JWT_SECRET_KEY", "dev-key-change-me")
WT_ALGORITHM = getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


ENVIRONMENT = getenv("ENVIRONMENT", "development")
DEBUG = getenv("DEBUG", "True").lower() == "true"