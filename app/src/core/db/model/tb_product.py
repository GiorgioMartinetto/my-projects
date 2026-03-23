"""
app/src/core/db/model/tb_product.py

Modello ORM SQLAlchemy per la tabella `products`.

Descrizione
-----------
Questo modulo definisce la classe `TbProduct`, che mappa la tabella dei prodotti
usata dal servizio. Il modello è pensato per rappresentare prodotti con:
- identificatore univoco (UUID salvato come stringa);
- nome univoco del prodotto;
- descrizione testuale opzionale;
- prezzo e quantità;
- riferimento al creatore tramite l'email (`users.email`);
- timestamp di creazione con timezone.

Note operative
--------------
- L'UUID viene memorizzato come stringa (`String(36)`) per massima portabilità tra DB.
- La colonna `name` è marcata `unique=True`: il vincolo viene fatto a livello DB;
  se vuoi un messaggio user-friendly per duplicati, intercetta l'eccezione del DB
  (es. `IntegrityError`) nel repository/service.
- `created_by` è definito come FK verso `users.email`; se preferisci relazionare con
  `users.id`, aggiorna il modello e i repository/servizi di conseguenza.
- `created_at` è pensato per essere salvato con timezone (UTC). Verifica la sorgente
  dell'import `UTC` nel progetto; in alcuni contesti si preferisce `datetime.now(timezone.utc)`.

Esempio rapido
-------------
# Creazione di un prodotto (concettuale, da eseguire in una sessione SQLAlchemy):
from src.core.db.model.tb_product import TbProduct
p = TbProduct(
    name="Tazza",
    description="Tazza in ceramica",
    price=12.5,
    quantity=10,
    created_by="mario@example.com"
)
session.add(p)
session.commit()

# Query esempio:
product = session.query(TbProduct).filter_by(name="Tazza").one_or_none()

"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.db.model import Base


class TbProduct(Base):
    """
    Product model for storing product information.

    Attributi principali
    - id: Unique identifier (UUID saved as string in String(36)).
      Viene generato automaticamente con uuid4() se non fornito.
    - name: Nome del prodotto (String, unique). Usato anche per ricerche leggibili.
    - description: Descrizione breve; opzionale.
    - price: Valore numerico del prezzo (tipo float).
    - quantity: Quantità disponibile (tipo int).
    - created_by: Email dell'utente creatore (FK -> users.email). Nota: FK usa email come
      riferimento nel modello attuale.
    - created_at: Timestamp di creazione con timezone (default: ora corrente, idealmente UTC).

    Buone pratiche
    - Non salvare mai password o dati sensibili in chiaro nei campi del prodotto.
    - Validare i campi (es. price >= 0, quantity >= 0) nel livello service prima di creare
      l'istanza per evitare eccezioni a runtime o record incoerenti.
    - Quando si effettuano operazioni di cancellazione, considerare la soft-delete se vuoi
      mantenere lo storico (es. colonna `is_deleted`).
    """

    __tablename__ = "products"

    # Identificatore primario: UUID memorizzato come stringa (formato standard 36 caratteri)
    id: Mapped[UUID[str]] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()), nullable=False
    )

    # Nome del prodotto: campo testuale, obbligatorio e univoco
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Descrizione opzionale del prodotto; lunghezza limitata a 255 caratteri
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Prezzo: usare il livello service per validare il formato e i vincoli (es. >= 0)
    # Nota: qui non è specificato il tipo SQL (es. Numeric); è lasciato al DB/ORM come
    # tipo Python float. Per precisione monetaria valutare Numeric/Decimal.
    price: Mapped[float] = mapped_column(nullable=False)

    # Quantità disponibile: integer non nullo
    quantity: Mapped[int] = mapped_column(nullable=False)

    # Creatore: riferimento all'email dell'utente che ha creato il prodotto.
    # FK verso `users.email` (stringa). Se cambi la relazione a use id, aggiornare la FK.
    created_by: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.email"), nullable=False
    )

    # Timestamp di creazione con timezone. Il default usa `datetime.now(UTC)` così come
    # presente nel codice; verifica coerenza con il resto del progetto (potrebbe
    # essere preferibile usare timezone.utc esplicitamente).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    def __repr__(self) -> str:
        # Rappresentazione utile per debugging/logging. Non deve esporre dati sensibili.
        return (
            f"<Product(id={self.id}, name={self.name}, price={self.price},"
            f"created_by={self.created_by}, created_at={self.created_at})>"
        )
