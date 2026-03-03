from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from src.core.config import settings

_db_config = settings.database

def _build_database_url() -> str:
    """
    Build the PostgreSQL DSN from the application settings.

    The password and user are URL-encoded to safely handle special characters.
    """
    password = quote_plus(_db_config.password)
    user = quote_plus(_db_config.user)
    host = _db_config.host
    port = _db_config.port
    name = _db_config.name
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL: str = _build_database_url()

engine: Engine = create_engine(
    DATABASE_URL,
    pool_size=_db_config.pool_size,
    max_overflow=_db_config.max_overflow,
    pool_timeout=_db_config.pool_timeout,
    pool_recycle=_db_config.pool_recycle,
    pool_pre_ping=_db_config.pool_pre_ping,
)

# "SessionLocal" is a factory for short-lived Session objects, typically one
# per HTTP request or Pub/Sub message handler.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_session() -> Session:
    """
    Return a new SQLAlchemy Session.

    The caller is responsible for closing the session or using the context
    manager helpers below.
    """
    return SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Example usage:

        with session_scope() as session:
            repo = RequestRepository(session)
            ...

    On success the transaction is committed; on any exception it is rolled back.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI-style dependency that yields a Session and ensures it is closed.

    The transaction boundaries are left to the caller (endpoint or service
    layer). This function only manages the lifecycle of the Session itself.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()