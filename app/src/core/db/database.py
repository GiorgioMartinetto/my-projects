"""
app.src.core.db.database
------------------------

Moduli e helper per la connessione al database usando SQLAlchemy.

Questo modulo:
- Costruisce la URL di connessione PostgreSQL (psycopg2) a partire dalle impostazioni
  dell'applicazione (vedi `src.core.config.settings.database`).
- Inizializza l'Engine SQLAlchemy condiviso dall'applicazione.
- Fornisce una factory `SessionLocal` per ottenere Session brevi (tipicamente
  una per richiesta HTTP).
- Fornisce due utilità per la gestione delle sessioni:
    - `session_scope()` : context manager che apre una sessione, fa commit al successo
      e rollback in caso di eccezione.
    - `get_db_session()` : generator-style dependency pensata per essere usata con
      FastAPI (yield-based dependency) che garantisce la chiusura della sessione.

Note importanti:
- Le credenziali (password, user) sono codificate con URL-encoding per permettere
  l'utilizzo di caratteri speciali.
- Le impostazioni del pool di connessione sono prese da `settings.database`.
- Questo modulo non effettua migrazioni né definisce modelli: si occupa solo della
  connettività e del ciclo di vita delle Session.
- Esempio d'uso:
    with session_scope() as session:
        # usare session...
        ...

    # In FastAPI:
    def endpoint(db: Session = Depends(get_db_session)):
        # usare db...
        ...

Autore: progetto sperimentale (documentazione aggiunta)
"""

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
    Costruisce la URL/DSN per PostgreSQL (psycopg2) a partire dalle impostazioni.

    Vengono applicati `quote_plus` a user e password per:
      - evitare problemi con caratteri speciali (es. @, :, /, spazio),
      - produrre una stringa sicura da inserire nella DSN.

    Ritorno:
        str: la DSN completa in formato accettato da SQLAlchemy, esempio:
             "postgresql+psycopg2://user:password@host:port/name"

    Esempio:
        >>> _build_database_url()
        'postgresql+psycopg2://alice:fake@db.example.com:5432/mydb'

    Nota:
        Questo helper dipende da `_db_config` che è preso da `settings.database`.
        Se le impostazioni non sono corrette la costruzione della URL può fallire.
    """
    password = quote_plus(_db_config.password)
    user = quote_plus(_db_config.user)
    host = _db_config.host
    port = _db_config.port
    name = _db_config.name
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL: str = _build_database_url()
"""La DSN completa usata per creare l'Engine SQLAlchemy.

Viene costruita una sola volta a import time; se hai bisogno di cambiare la
config durante il runtime devi ricreare l'engine manualmente.
"""

# Creazione dell'Engine SQLAlchemy condiviso. Le opzioni del pool sono lette dal
# file di configurazione per adattare il comportamento al carico dell'app.
#
# Parametri usati (esempi):
# - pool_size: numero di connessioni persistenti nel pool
# - max_overflow: connessioni extra che possono essere aperte oltre pool_size
# - pool_timeout: tempo di attesa per ottenere una connessione dal pool
# - pool_recycle: dopo quanti secondi riciclare la connessione
# - pool_pre_ping: se True, verifica la connessione prima di usarla
engine: Engine = create_engine(
    DATABASE_URL,
    pool_size=_db_config.pool_size,
    max_overflow=_db_config.max_overflow,
    pool_timeout=_db_config.pool_timeout,
    pool_recycle=_db_config.pool_recycle,
    pool_pre_ping=_db_config.pool_pre_ping,
)

# "SessionLocal" è una factory che crea Session SQLAlchemy a breve vita.
# Tipicamente si usa una Session per richiesta HTTP; evitare di condividere
# oggetti Session tra thread o richieste.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_session() -> Session:
    """
    Restituisce una nuova istanza di SQLAlchemy Session.

    Uso:
        session = get_session()
        try:
            # operazioni sul db
        finally:
            session.close()

    Ritorno:
        sqlalchemy.orm.Session: una sessione nuova non ancora chiusa.

    Nota:
        Questo helper non gestisce il commit/rollback: la responsabilità ricade
        sul chiamante. Per comportamento transazionale automatico, utilizzare
        `session_scope()` o gestire esplicitamente commit/rollback.
    """
    return SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Un context manager che fornisce un ambito transazionale.

    Comportamento:
    - apre una nuova Session,
    - lascia eseguire il blocco chiamante,
    - fa commit se il blocco termina senza eccezioni,
    - fa rollback e rilancia l'eccezione in caso di errore,
    - chiude sempre la Session alla fine.

    Esempio:
        with session_scope() as session:
            # eseguire operazioni sul DB usando `session`
            # in caso di eccezione verrà fatto rollback automaticamente

    Ritorno:
        Generator[Session, None, None]: fornisce l'oggetto Session al blocco.
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
    Dependency in stile FastAPI che yield-a una Session e la chiude al termine.

    Uso tipico (FastAPI):
        @router.get("/items")
        def read_items(db: Session = Depends(get_db_session)):
            items = db.query(ItemModel).all()
            return items

    Caratteristiche:
    - Si limita a gestire il ciclo di vita (apre e chiude la sessione).
    - Non effettua commit né rollback automaticamente: i confini della
      transazione sono responsabilità dell'end-point o del servizio chiamante.

    Ritorno:
        Generator[Session, None, None]: yield di una Session pronta all'uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
