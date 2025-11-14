"""
Gerenciamento de conexão com banco de dados
Suporta PostgreSQL, SQLite e MySQL
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool, QueuePool
from src.config import DATABASE_URL, ENVIRONMENT, DEBUG

SLOW_QUERY_THRESHOLD = float(os.getenv("SLOW_QUERY_THRESHOLD", "0.5"))

# Configuração do engine baseada no ambiente
if ENVIRONMENT == 'production':
    # Produção: Pool de conexões otimizado
    engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=10, max_overflow=20, pool_pre_ping=True,
                           pool_recycle=3600, echo=False)
elif ENVIRONMENT == 'testing':
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=NullPool, echo=False)
else:
    engine = create_engine(DATABASE_URL, echo=DEBUG, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Ativa Foreign Keys no SQLite (desativado por padrão)
    """
    if engine.dialect.name == "sqlite":
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    """
    Log de queries lentas (apenas em desenvolvimento)
    """
    if DEBUG and ENVIRONMENT == 'development':
        import time
        conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    """
    Log de queries lentas (apenas em desenvolvimento)
    """
    if DEBUG and ENVIRONMENT == 'development':
        import time
        total = time.time() - conn.info['query_start_time'].pop(-1)
        if total > SLOW_QUERY_THRESHOLD:
            print(f"⚠️ Query lenta ({total:.2f}s): {statement[:100]}...")


# ==================== Dependency para FastAPI ====================

def get_db():
    """
    Dependency para obter sessão do banco em rotas FastAPI

    Usage:
        @router.get("/usuarios")
        def listar_usuarios(db: Session = Depends(get_db)):
            return db.query(Usuario).all()
    """
    from src.database.session import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
