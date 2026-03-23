"""
app/src/core/db/model/tb_user.py

Modulo: modello SQLAlchemy per la tabella `users`.

Descrizione generale
-------------------
Questo modulo definisce la classe `TbUser`, una mappatura ORM (SQLAlchemy) della tabella
`users` usata per la gestione degli utenti (autenticazione e profili).
La classe utilizza l'API ORM moderna (`Mapped`, `mapped_column`) per definire colonne e
metadati. I commenti e le docstring qui presenti spiegano a livello pratico lo scopo dei
campi, i vincoli più importanti e come usare il modello in contesti tipici.

Note importanti:
- L'identificatore `id` è generato come UUID convertito in stringa e memorizzato in una
  colonna `String(36)`. Questo approccio rende il campo portabile tra DB differenti.
- L'email è marcata `unique=True` e `index=True` per rendere efficienti le lookup e
  far rispettare l'unicità a livello DB.
- `created_at` è pensato per essere salvato con timezone. Assicurati che il valore di default
  imposti effettivamente un timestamp UTC (dipende dall'import usato per `UTC`).
- `password_hash` contiene l'hash della password (non salvare mai la password in chiaro).
- Se modifichi il modello (aggiunta/alterazione colonne), ricorda di aggiornare le migration
  del progetto (es. Alembic) se presenti.

Esempio rapido d'uso (concettuale)
---------------------------------
# Creazione di un'istanza (in un contesto con sessione SQLAlchemy):
user = TbUser(email="mario@example.com", username="mario", password_hash="<bcrypt-hash>")
session.add(user)
session.commit()

# Query (esempio):
user = session.query(TbUser).filter_by(email="mario@example.com").one_or_none()

# Nota: nel progetto le operazioni di persistenza sono normalmente incapsulate in
# repository/service; non eseguire commit direttamente dalla logica di business se il
# progetto richiede un controllo centrale delle transazioni.

"""
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db.model import Base


class TbUser(Base):
    """
    Rappresenta la tabella `users`.

    Questo modello definisce i campi usati per l'autenticazione e per l'account utente.

    Campi principali
    - id: identificatore primario (UUID memorizzato come stringa).
      Generato automaticamente tramite uuid4; la colonna è String(36).
    - email: indirizzo email dell'utente, unico e indicizzato.
    - username: nome pubblico dell'utente (non unique nel modello attuale).
    - password_hash: hash della password (es. bcrypt). Non salvare password in chiaro.
    - created_at: timestamp di creazione (con timezone).
    - is_active: flag booleano che indica se l'account è attivo.

    Considerazioni di sicurezza e pratiche consigliate
    - Conservare solo hash sicuri delle password (bcrypt/argon2).
    - Validare email e username a livello di servizio prima di creare l'utente.
    - Gestire le eccezioni di unicità dell'email (IntegrityError) a livello di repository/service
      per fornire feedback utente-friendly.
    - Per tracciare modifiche, valuta l'aggiunta di un campo `updated_at` con `onupdate`.
    """

    __tablename__ = "users"

    # Campo primario: UUID memorizzato come stringa (es. "550e8400-e29b-41d4-a716-446655440000")
    id: Mapped[UUID[str]] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False
    )

    # Email dell'utente: unica e indicizzata per ricerche rapide
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Nome utente: campo testuale; se si desidera unicità, aggiungere unique=True
    username: Mapped[str] = mapped_column(String(255), nullable=False)

    # Hash della password (es. hash bcrypt) - mai salvare la password in chiaro
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamp di creazione con timezone; assicurarsi che il default usi UTC
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Flag che indica se l'account è attivo (abilitato)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        """
        Rappresentazione testuale dell'istanza utile per logging/debug.

        Non includere informazioni sensibili (es. password_hash) nella rappresentazione.
        """
        return (
            f"<User(id={self.id}, email={self.email}, username={self.username},"
            f" is_active={self.is_active})>"
        )
