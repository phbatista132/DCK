from sqlalchemy.orm import sessionmaker, scoped_session, Session
from typing import Generator
from src.database.connection import engine

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

ScopedSession = scoped_session(SessionLocal)

def get_session() -> Generator[Session, None, None]:
    """
    Retorna nova sessão do banco.
    Usar em contextos que não são FastAPI.

    Exemplo:
        with get_session() as db:
            usuarios = db.query(Usuario).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()