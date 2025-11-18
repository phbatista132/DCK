"""
Checklist de Deploy - Validar tudo antes de subir para produção
Execute: python deploy_checklist.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime


class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def check(condition: bool, message: str, critical: bool = True) -> bool:
    """Verifica condição e imprime resultado"""
    if condition:
        print(f"{Color.GREEN}✅ {message}{Color.END}")
        return True
    else:
        icon = "❌" if critical else "⚠️"
        color = Color.RED if critical else Color.YELLOW
        print(f"{color}{icon} {message}{Color.END}")
        return not critical


def main():
    print("\n" + "=" * 60)
    print(f"{Color.BLUE}🚀 CHECKLIST DE DEPLOY - {datetime.now().strftime('%d/%m/%Y %H:%M')}{Color.END}")
    print("=" * 60 + "\n")

    all_ok = True

    # ==================== 1. ARQUIVOS ESSENCIAIS ====================
    print(f"{Color.BLUE}📁 1. Verificando Arquivos Essenciais{Color.END}")
    print("-" * 60)

    essential_files = [
        ("requirements.txt", True),
        ("Procfile", True),
        (".env.example", True),
        ("init_db.py", False),
        ("README.md", False),
        ("alembic.ini", True),
    ]

    for file, critical in essential_files:
        exists = Path(file).exists()
        all_ok &= check(exists, f"{file} existe", critical)

    # ==================== 2. VARIÁVEIS DE AMBIENTE ====================
    print(f"\n{Color.BLUE}🔐 2. Verificando Variáveis de Ambiente{Color.END}")
    print("-" * 60)

    from dotenv import load_dotenv
    load_dotenv()

    env_vars = [
        ("DATABASE_URL", True),
        ("JWT_SECRET_KEY", True),
        ("ENVIRONMENT", False),
    ]

    for var, critical in env_vars:
        exists = os.getenv(var) is not None
        all_ok &= check(exists, f"{var} configurada", critical)

    # ==================== 3. DEPENDÊNCIAS ====================
    print(f"\n{Color.BLUE}📦 3. Verificando Dependências{Color.END}")
    print("-" * 60)

    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "pydantic",
        "python-jose",
        "bcrypt",
        "psycopg2-binary",
    ]

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            check(True, f"{package} instalado")
        except ImportError:
            all_ok &= check(False, f"{package} NÃO instalado", True)

    # ==================== 4. ESTRUTURA DO PROJETO ====================
    print(f"\n{Color.BLUE}🏗️ 4. Verificando Estrutura do Projeto{Color.END}")
    print("-" * 60)

    required_dirs = [
        "src/api",
        "src/controllers",
        "src/database",
        "src/models",
        "src/services",
        "alembic/versions",
    ]

    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        all_ok &= check(exists, f"Diretório {dir_path} existe", True)

    # ==================== 5. TESTES ====================
    print(f"\n{Color.BLUE}🧪 5. Verificando Testes{Color.END}")
    print("-" * 60)

    test_exists = Path("tests").exists()
    check(test_exists, "Diretório de testes existe", False)

    if test_exists:
        import subprocess
        try:
            result = subprocess.run(
                ["pytest", "--co", "-q"],
                capture_output=True,
                text=True,
                timeout=10
            )
            num_tests = len([line for line in result.stdout.split('\n') if '::test_' in line])
            check(num_tests > 0, f"{num_tests} testes encontrados", False)
        except Exception as e:
            check(False, f"Erro ao verificar testes: {e}", False)

    # ==================== 6. MIGRATIONS ====================
    print(f"\n{Color.BLUE}🔄 6. Verificando Migrations{Color.END}")
    print("-" * 60)

    migrations_dir = Path("alembic/versions")
    if migrations_dir.exists():
        migrations = list(migrations_dir.glob("*.py"))
        migrations = [m for m in migrations if m.name != "__pycache__"]
        check(len(migrations) > 0, f"{len(migrations)} migration(s) encontrada(s)", True)
    else:
        all_ok &= check(False, "Diretório de migrations não existe", True)

    # ==================== 7. CONFIGURAÇÕES DE SEGURANÇA ====================
    print(f"\n{Color.BLUE}🔒 7. Verificando Segurança{Color.END}")
    print("-" * 60)

    # Verificar .gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        checks = [
            (".env" in content, ".env no .gitignore"),
            ("__pycache__" in content, "__pycache__ no .gitignore"),
            ("*.db" in content, "*.db no .gitignore"),
        ]
        for condition, msg in checks:
            all_ok &= check(condition, msg, True)
    else:
        all_ok &= check(False, ".gitignore existe", True)

    # Verificar JWT_SECRET_KEY não é default
    jwt_key = os.getenv("JWT_SECRET_KEY", "")
    is_secure = jwt_key != "dev-key-change-me" and len(jwt_key) > 20
    all_ok &= check(is_secure, "JWT_SECRET_KEY é segura", True)

    # ==================== 8. BANCO DE DADOS ====================
    print(f"\n{Color.BLUE}🗄️ 8. Verificando Conexão com Banco{Color.END}")
    print("-" * 60)

    try:
        from src.database.connection import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            check(True, "Conexão com banco OK")
    except Exception as e:
        all_ok &= check(False, f"Erro ao conectar: {str(e)[:50]}", True)

    # ==================== RESULTADO FINAL ====================
    print("\n" + "=" * 60)
    if all_ok:
        print(f"{Color.GREEN}✅ TUDO OK! PRONTO PARA DEPLOY{Color.END}")
        print("=" * 60)
        print(f"\n{Color.BLUE}📝 Próximos passos:{Color.END}")
        print("1. Commitar mudanças: git add . && git commit -m 'Preparar deploy'")
        print("2. Push para GitHub: git push origin main")
        print("3. Configurar Railway.app e conectar repositório")
        print("4. Adicionar PostgreSQL no Railway")
        print("5. Configurar variáveis de ambiente no Railway")
        print("6. Deploy automático!")
        return 0
    else:
        print(f"{Color.RED}❌ EXISTEM PROBLEMAS QUE PRECISAM SER CORRIGIDOS{Color.END}")
        print("=" * 60)
        print(f"\n{Color.YELLOW}Corrija os itens marcados com ❌ antes de fazer deploy{Color.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())