"""
Script para criar migrations com Alembic
Execute: python create_migrations.py
"""
import os
import subprocess
from pathlib import Path


def setup_alembic():
    """Configura Alembic e cria primeira migration"""

    print("🚀 Configurando Alembic...")

    # 1. Inicializar Alembic (se ainda não foi)
    if not Path("alembic").exists():
        print("📁 Inicializando Alembic...")
        subprocess.run(["alembic", "init", "alembic"])
        print("✅ Alembic inicializado")

    # 2. Configurar alembic/env.py
    print("\n📝 Configurando env.py...")
    env_content = '''
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATABASE_URL
from src.database.models import Base

# this is the Alembic Config object
config = context.config

# Sobrescrever sqlalchemy.url com a variável do .env
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    with open("alembic/env.py", "w", encoding="utf-8") as f:
        f.write(env_content)
    print("✅ env.py configurado")

    # 3. Criar primeira migration
    print("\n📦 Criando primeira migration...")
    subprocess.run([
        "alembic", "revision", "--autogenerate",
        "-m", "Initial migration: create all tables"
    ])
    print("✅ Migration criada")

    print("\n" + "=" * 50)
    print("✅ ALEMBIC CONFIGURADO COM SUCESSO!")
    print("=" * 50)
    print("\n📝 Próximos passos:")
    print("1. Revisar migration em: alembic/versions/")
    print("2. Aplicar migration: alembic upgrade head")
    print("3. Verificar tabelas criadas")


if __name__ == "__main__":
    setup_alembic()