"""
Alembic Environment Configuration
Configuração melhorada para desenvolvimento e produção
"""
import sys
import os
from pathlib import Path

# Adicionar src ao PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import logging
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Importar Base e carregar variáveis de ambiente
from dotenv import load_dotenv

load_dotenv()

from src.database.models import Base

# ==================== CONFIGURAÇÃO ====================

# Obter DATABASE_URL do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")

# Se não existir, usar SQLite local (desenvolvimento)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./data/loja.db"
    print("⚠️  DATABASE_URL não definida. Usando SQLite local.")

# Fix para Railway/Heroku (postgres:// → postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("🔧 Convertendo postgres:// para postgresql://")

# Configurar Alembic
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Metadata dos models
target_metadata = Base.metadata


# ==================== FUNÇÕES DE MIGRAÇÃO ====================

def run_migrations_offline():
    """
    Run migrations in 'offline' mode.

    Gera SQL sem conectar ao banco.
    Útil para gerar scripts de migração.
    """
    logger.info("Executando migração OFFLINE...")

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detectar mudanças de tipo
        compare_server_default=True  # Detectar mudanças de default
    )

    with context.begin_transaction():
        context.run_migrations()

    logger.info("Migração OFFLINE concluída.")


def run_migrations_online():
    """
    Run migrations in 'online' mode.

    Conecta ao banco e executa migrations.
    Usado em desenvolvimento e produção.
    """
    logger.info("Executando migração ONLINE...")

    # Configuração do engine
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL

    # Pool de conexões
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Sem pool em migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detectar mudanças de tipo
            compare_server_default=True,  # Detectar mudanças de default
            include_schemas=True,  # Incluir schemas

            # Renderizar valores de forma segura
            render_as_batch=True,  # Para SQLite (ALTER TABLE)

            # Transações
            transaction_per_migration=True,  # Uma transação por migration
        )

        with context.begin_transaction():
            context.run_migrations()

    logger.info("✅ Migração ONLINE concluída.")


# ==================== EXECUÇÃO ====================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()