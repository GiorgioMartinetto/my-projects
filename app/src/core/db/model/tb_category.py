"""
Modulo: app.src.core.db.model.tb_category

Definizione del modello ORM per la tabella "categories".

Questo modulo contiene la classe TbCategory, una mappatura SQLAlchemy per la
tabella delle categorie dell'applicazione. La tabella memorizza:
- id: identificatore UUID (stringa) generato automaticamente via uuid4()
- category_name: nome della categoria, unico e non nullo
- created_by: riferimento all'email dell'utente che ha creato la categoria (FK -> users.email)
- created_at: timestamp UTC di creazione, con timezone e valore di default

Nota:
- I default sono forniti come callables (lambda) per evitare valori condivisi
  tra istanze e per garantire che il valore venga valutato al momento dell'istanza.
- Il campo `created_at` utilizza timezone-aware datetime con UTC.
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db.model import Base


class TbCategory(Base):
    """
    Modello ORM per la tabella "categories".

    Campi:
    - id (str UUID): chiave primaria, stringa di lunghezza 36, default -> uuid4()
      Utilizzare stringhe per conservare compatibilità semplice con JSON/UUID nei payload.
    - category_name (str): nome della categoria, massimo 255 caratteri, unico e non nullo.
      Vincolo UNIQUE per prevenire duplicati.
    - created_by (str): email dell'utente creatore; chiave esterna verso users.email.
      Questo campo permette di tracciare l'autore della creazione della categoria.
    - created_at (datetime): timestamp timezone-aware (UTC) dell'istante di creazione.
      Default impostato al momento dell'istanza tramite datetime.now(UTC).

    Uso:
    - Istanziare e popolare i campi prima di aggiungere l'oggetto alla sessione SQLAlchemy.
    - Il repr restituisce una rappresentazione sintetica utile per logging/debug.

    Esempio rapido:
        cat = TbCategory(category_name="Elettronica", created_by="user@example.com")
        session.add(cat)
        session.commit()
    """

    __tablename__ = "categories"

    # Identificatore univoco della categoria; memorizzato come stringa UUID (36)
    id: Mapped[UUID[str]] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False
    )

    # Nome leggibile della categoria; obbligatorio e unico
    category_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Email dell'utente che ha creato la categoria; FK verso users.email
    created_by: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.email"), nullable=False
    )

    # Timestamp di creazione (timezone-aware, UTC); default valutato al runtime
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    def __repr__(self) -> str:
        """
        Rappresentazione testuale compatta dell'istanza.

        Viene usata principalmente per logging e debugging, mostra l'id e
        il nome della categoria. Non include campi sensibili.
        """
        return f"<TbCategory(id={self.id}, category_name={self.category_name})>"
