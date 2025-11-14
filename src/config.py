from os import getenv
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(".env")

ROOT_DIR = Path(".").resolve()
DATA_DIR = ROOT_DIR / "database"

JWT_SECRET_KEY = getenv("JWT_SECRET_KEY", "dev-key-change-me")
WT_ALGORITHM = getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


ENVIRONMENT = getenv('ENVIRONMENT', 'development')  # production, staging, development
DEBUG = getenv('DEBUG', 'True').lower() == 'true'

# URL do banco de dados
DATABASE_URL = getenv('DATABASE_URL','sqlite:///./data/loja.db')



# Configurações de pool (para PostgreSQL/MySQL)
DB_POOL_SIZE = int(getenv('DB_POOL_SIZE', '10'))
DB_MAX_OVERFLOW = int(getenv('DB_MAX_OVERFLOW', '20'))