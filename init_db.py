import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.database.connection import engine
from src.database.models import criar_todas_tabelas, Usuarios
from src.services.security.password_handler import PasswordHandler
from src.database import SessionLocal


def criar_admin_padrao():
    """Cria usuário admin padrão"""
    db = SessionLocal()

    try:
        # Verificar se já existe
        admin = db.query(Usuarios).filter(Usuarios.username == 'admin').first()

        if not admin:
            senha_hash = PasswordHandler.hash_password('Admin123!')

            admin = Usuarios(
                username='admin',
                email='admin@loja.com',
                senha_hash=senha_hash,
                nome_completo='Administrador',
                tipo_usuario='admin'
            )

            db.add(admin)
            db.commit()

            print("Admin criado!")
            print("Username: admin")
            print("Senha: Admin123!")
        else:
            print("Admin já existe")

    except Exception as e:
        print(f"Erro: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    print("🚀 Inicializando banco de dados...\n")

    # 1. Criar tabelas
    print("1️⃣ Criando tabelas...")
    criar_todas_tabelas(engine)

    # 2. Criar admin
    print("\n2️⃣ Criando admin...")
    criar_admin_padrao()

    print("\n✅ Banco inicializado!")