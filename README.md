# Product Store Manager

## Introduzione
Questo progetto è un servizio REST sperimentale scritto in Python, pensato per imparare a progettare e sviluppare un'applicazione ben strutturata con FastAPI, persistenza tramite SQLAlchemy/Postgres, gestione utenti e funzionalità CRUD per i prodotti. L'obiettivo principale è fornire una codebase modulare, testabile e facilmente estendibile.

### Indice
- [Funzionalità Core](#funzionalità-core):
  - [Configurazione](#configurazione)
  - [Security](#security)
  - [Logger](#logger)
- [Database](#database):
  - [Models](#models)
  - [Repository](#repository)
- [API](#api):
  - [User Endpoint](#user-endpoint)
  - [Product Endpoint](#product-endpoint)
  - [Category Endpoint](#category-endpoint)

Alberatura della cartella `app`

```
app/
├── __init__.py
├── config/
│   └── config.yml
└── src/
	├── __init__.py
	├── main.py
	├── core/
	│   ├── __init__.py
	│   ├── config.py
	│   ├── logger.py
	│   ├── security.py
	│   └── db/
	│       ├── __init__.py
    │       ├── database.py
    │       ├── model/
    │       │   ├── __init__.py 
    │       │   ├── base.py
    │       │   ├── tb_category_repository.py
    │       │   ├── tb_product_repository.py
    │       │   └── tb_user_repository.py
    │       └── repository/
    │           ├── __init__.py 
    │           ├── base.py
    │           ├── tb_category_repository.py
    │           ├── tb_product_repository.py
    │           └── tb_user_repository.py
	├── exceptions/
	│   ├── __init__.py
	│   ├── base_exception.py
	│   ├── product_exceptions/
	│   └── user_exceptions/
	├── models/
	├── routers/
	│   ├── __init__.py
	│   ├── deps.py
	│   └── v1/
	│       ├── __init__.py
	│       ├── category_endpoint.py
	│       ├── product_endpoint.py
	│       └── user_endpoint.py
	├── schemas/
	│   ├── __init__.py
	│   ├── category_request.py
	│   ├── category_response.py
	│   ├── product_request.py
	│   ├── product_response.py
	│   ├── user_request.py
	│   └── user_response.py
	└── services/
		├── __init__.py
		├── products/
        │   ├── __init__.py
        │   ├── category_service.py
        │   └── product_service.py
		└── users/
            ├── __init__.py
            └── user_service.py
```
## Funzionalità Core
### Configurazione
Il file di configurazione `config.yml` si trova nella cartella `app/config/`.

La configurazione del progetto è pensata per essere semplice da gestire anche senza entrare troppo nei dettagli tecnici.

In pratica, l'applicazione legge le impostazioni da due fonti:

- `app/config/config.yml`, che contiene la configurazione di base del progetto;
- `env/local.env`, che permette di personalizzare alcuni valori senza modificare direttamente il file YAML.

Il funzionamento logico è questo:

1. l'applicazione carica i valori principali dal file `config.yml`;
2. se trova una variabile d'ambiente corrispondente in `env/local.env`, usa quel valore al posto di quello presente nel file YAML;
3. in questo modo il file YAML rimane una base comune, mentre le variabili d'ambiente servono per adattare il progetto a un ambiente specifico o a esigenze locali.

Questo approccio è utile perché separa la configurazione "standard" del progetto dalle personalizzazioni locali.

#### Come leggere i nomi delle variabili d'ambiente

I nomi delle variabili seguono una regola semplice: vengono costruiti a partire dalla sezione e dal campo della configurazione, scritti in maiuscolo e separati da `_`.

Ad esempio:

- `app.port` diventa `APP_PORT`
- `app.debug` diventa `APP_DEBUG`
- `database.host` diventa `DATABASE_HOST`
- `token.secret_key` diventa `TOKEN_SECRET_KEY`

Se il valore rappresenta un numero o un booleano, l'applicazione lo interpreta automaticamente nel formato corretto.

#### Esempio pratico per un utente non tecnico

Supponiamo che tu voglia:

- cambiare la porta dell'applicazione;
- attivare la modalità debug;
- modificare l'host del database.

Senza toccare il codice, puoi aggiungere o aggiornare il file `env/local.env` in questo modo:

```env
APP_PORT=9000
APP_DEBUG=true
DATABASE_HOST=localhost
```

In questo caso:

- l'app continuerà a usare `config.yml` come base;
- i tre valori sopra avranno priorità rispetto a quelli scritti nel file YAML;
- tutte le altre configurazioni resteranno invariate.

#### Quando usare `config.yml` e quando usare `local.env`

- usa `config.yml` per i valori di base del progetto, condivisi da tutti;
- usa `env/local.env` per personalizzazioni locali, prove, override o valori che possono cambiare da un ambiente all'altro.

Se vuoi partire da un modello, puoi prendere come riferimento anche `env/example.env`.

> Nota: questo meccanismo funziona per le configurazioni già previste dal progetto. Se in futuro vorrai introdurre una configurazione completamente nuova, sarà necessario aggiungerla anche nella struttura di configurazione dell'applicazione.

### Security

Questo file documenta il modulo `app/src/core/security.py`, che contiene le funzioni usate per la gestione delle password e la creazione dei token di accesso (JWT).

Panoramica
- Scopo: fornire funzioni di utilità per l'hashing/verifica delle password e per la generazione di token JWT usati dall'applicazione per l'autenticazione.
- Dipendenze principali: `bcrypt` (per l'hashing sicuro delle password) e `python-jose` (per la codifica dei JWT).

API e comportamento

- hash_password(password: str) -> str
  - Riceve una password in chiaro (stringa) e ritorna la versione hashed (stringa) usando bcrypt.
  - Uso tipico: salvare il valore restituito nel database invece della password in chiaro.

- verify_password(plain_password: str, hashed_password: str | bytes) -> bool
  - Controlla se la password in chiaro corrisponde all'hash memorizzato.
  - Ritorna True se la password è corretta, False altrimenti.

- create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str
  - Genera un JSON Web Token (JWT) firmato contenente i dati forniti in `data` e un campo di scadenza `exp`.
  - Se `expires_delta` non è fornito, viene usata una scadenza di default (es.: 15 minuti).
  - Il token è firmato usando la chiave e l'algoritmo presenti in `settings.token` (vedi `app/src/core/config.py`).

Esempi di utilizzo

1) Hashare una password prima di salvarla:

```python
from src.core.security import hash_password

raw = "mia_password"
hashed = hash_password(raw)
# salva `hashed` nel database
```

2) Verificare la password al login:

```python
from src.core.security import verify_password

# Esempio autosufficiente: ricava l'hash e poi verifica
plain_password_input = "mia_password"
from src.core.security import hash_password
stored_hashed_password = hash_password(plain_password_input)
is_valid = verify_password(plain_password_input, stored_hashed_password)
if is_valid:
	# procedi con autenticazione
	pass
```

3) Creare un token d'accesso (esempio minimo):

```python
from datetime import timedelta
from src.core.security import create_access_token

payload = {"sub": "user-id-123", "role": "user"}
token = create_access_token(payload, expires_delta=timedelta(hours=1))
# restituisci il token al client
```

Note pratiche e consigli di sicurezza
- Mantieni segreta la chiave usata per firmare i token (configurata in `settings.token.secret_key`).
- Imposta una scadenza adeguata per i token: valori troppo lunghi aumentano il rischio in caso di fuga delle credenziali.
- Usa sempre HTTPS in produzione per proteggere i token e le password durante il trasporto.
- Non memorizzare mai password in chiaro; conserva solo gli hash generati da `hash_password`.
- Se cambi l'algoritmo di firma o la chiave, valuta la necessità di invalidare i token precedenti.

### Logger
Questo file documenta il modulo `app/src/core/logger.py`, che configura il logging dell'applicazione usando `loguru` e fornisce una middleware per iniettare un `request_id` nelle entry di log.

Panoramica
- Scopo: centralizzare il setup del logger, formattare i messaggi (JSON o testo leggibile), inviarli su stdout e, opzionalmente, su file; intercettare il logging della stdlib per convogliarlo in `loguru`.
- Principali caratteristiche:
  - formattazione JSON o testuale a seconda della configurazione;
  - supporto per file di log con rotazione e retention;
  - iniezione di un `request_id` per collegare log e richieste HTTP;
  - intercettazione del logging della libreria stdlib (es. `uvicorn`) per evitare duplicazioni.

Componenti principali

- InterceptHandler(logging.Handler)
  - Handler che reindirizza i record del logging stdlib a `loguru.logger`, preservando livello ed eccezioni.

- setup_logger() -> loguru.Logger
  - Rimuove le configurazioni di default di `loguru` e aggiunge due handler principali:
	1. stdout (sempre abilitato)
	2. file (se `settings.logging.file_enabled` è True)
  - Applica il formato scelto: JSON (utile per sistemi di raccolta centralizzata) oppure testo colorato per sviluppo.
  - Regola: livello, backtrace, diagnose, enqueue (per thread/process safety) e filtri.
  - Intercetta il logging stdlib impostando un `InterceptHandler` e svuota i handler di `uvicorn` per evitare doppie righe.

- LoggingMiddleware (BaseHTTPMiddleware)
  - Middleware FastAPI che genera (o recupera) un `request_id` per ogni richiesta HTTP e lo rende disponibile tramite una ContextVar.
  - Inserisce l'header `X-Request-ID` nella risposta e assicura che il `request_id` sia resettato al termine della richiesta.
  - Il `request_id` viene poi aggiunto automaticamente a tutte le entry di log tramite il filtro `inject_request_id` usato negli handler.

Impostazioni rilevanti (da `settings.logging`)
- `json_format`: se True usa formato JSON; altrimenti formato leggibile (colorato).
- `level`: livello di logging (es. `INFO`, `DEBUG`).
- `colorize`: abilita/disabilita la colorazione nel terminale.
- `backtrace`, `diagnose`: aiutano nel debugging mostrando più informazioni nelle eccezioni.
- `enqueue`: se True abilita coda per scrivere i log in modo thread/process-safe.
- `file_enabled`: abilita la scrittura su file.
- `file_path`, `rotation`, `retention`: percorso, policy di rotazione e conservazione dei file di log.

Esempi d'uso

1) Inizializzare il logger all'avvio dell'app (es. in `main.py`):

```python
from fastapi import FastAPI
from src.core.logger import setup_logger, LoggingMiddleware

app = FastAPI()
# inizializza log e ottieni istanza di loguru
logger = setup_logger()
# registra la middleware per iniettare request_id
app.add_middleware(LoggingMiddleware)

logger.info("Logger inizializzato")
```

2) Usare il logger in un modulo qualsiasi dell'app:

```python
from src.core.logger import setup_logger

logger = setup_logger()
logger.debug("Esempio di messaggio di debug")
```

3) Comportamento della middleware e header
- Per ogni richiesta, se il client non invia `X-Request-ID`, la middleware genera un UUID e lo inserisce nella risposta sotto `X-Request-ID`.
- Nei log comparirà sempre il valore di `request_id` (se presente) permettendo di correlare le entry generate durante una singola richiesta.

Note operative e consigli
- In ambiente di sviluppo il formato testuale rende i log più leggibili; in produzione valuta JSON per integrazione con ELK/Graylog/Datadog.
- Assicurati che `settings.logging.file_path` punti a una directory esistente o che l'app abbia i permessi per crearla (il logger tenta di creare le directory necessarie).
- L'opzione `enqueue` è utile quando l'app lavora con più thread o processi (es. gunicorn/uvicorn workers).
- Rimuovere gli handler di `uvicorn` evita duplicate entry; non effettuare ulteriori configurazioni di logging a livello di comando se già gestite dal modulo.
- Se usi container o orchestratori, preferisci l'invio su stdout/stderr e lascia alla piattaforma la raccolta centralizzata dei log.

## Database
La sezione Database descrive la struttura delle tabelle (Models), il pattern usato per i repository (operazioni CRUD) e il funzionamento della comunicazione con il database tramite `app/src/core/db/database.py`.
### Comunicazione con il database — `app/src/core/db/database.py`

Il file `database.py` centralizza la costruzione della connessione e la gestione delle sessioni SQLAlchemy. I punti chiave del comportamento sono:

- Costruzione della DSN: `_build_database_url()` usa i valori di `settings.database` e `quote_plus` per codificare correttamente user/password con caratteri speciali, restituendo una URL come `postgresql+psycopg2://user:pass@host:port/dbname`.
- Creazione dell'engine: `create_engine(DATABASE_URL, ...)` viene configurato con i parametri di pooling presi dalle impostazioni (`pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`, `pool_pre_ping`). Questo permette ottimizzazioni di performance e affidabilità in produzione.
- SessionLocal: factory di sessioni (`sessionmaker`) configurata con `autocommit=False`, `autoflush=False` e `expire_on_commit=False` per un comportamento prevedibile delle entità dopo commit.
- Helper per ottenere sessioni:
  - `get_session()` — restituisce una nuova `Session`; il chiamante è responsabile di chiuderla.
  - `session_scope()` — context manager che fornisce una sessione e gestisce commit/rollback automaticamente: commit se tutto va a buon fine, rollback in caso di eccezione, e chiusura nel finally.
  - `get_db_session()` — generator compatibile con FastAPI `Depends` che yielda una Session e garantisce la chiusura al termine della richiesta.

Esempio pratico 1 — usare il context manager `session_scope` in un comando o in uno script:

```python
from src.core.db.database import session_scope
from src.core.db.repository.tb_user_repository import UserRepository

with session_scope() as session:
    repo = UserRepository(session)
    user = repo.create({"username": "pippo", "email": "p@example.com", "hashed_password": "..."})
    # alla fine del blocco la transazione verrà committata automaticamente
```

Esempio pratico 2 — usare `get_db_session` come dipendenza in FastAPI (gestione del lifecycle della sessione):

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from src.core.db.database import get_db_session

def some_service(db: Session = Depends(get_db_session)):
    # qui il service usa la session fornita; la chiusura è gestita da get_db_session
    pass
```

Nota operativa
- `session_scope()` è comodo per script, migration helper o task che devono definire chiaramente i confini della transazione.
- `get_db_session()` è pensato per l'integrazione con FastAPI e per garantire che ogni richiesta abbia una sessione isolata e correttamente chiusa.
- Tenere le configurazioni di pool nell'engine aiuta a ridurre la latenza in ambienti con carico elevato e a gestire correttamente la riconnessione.

### Models

Le tabelle principali mappate con SQLAlchemy nella codebase sono organizzate nella cartella `app/src/core/db/model` e rappresentano i concetti persistenti dell'applicazione. A titolo esemplificativo (la struttura reale si trova nei file `.py` nella cartella indicata):

- tb_user
  - campi: `id` (PK, UUID memorizzato come stringa), `username`, `email` (unique, indexed), `password_hash`, `is_active`, `created_at` (UTC).
  - scopo: memorizzare gli utenti dell'applicazione e i dati necessari per l'autenticazione e l'autorizzazione. Nota: nel modello attuale `email` è marcata come unique/indexed; `username` non è marcato come unique (se desideri unicità per username va aggiunta esplicitamente al modello e al repository).

- tb_category
 - tb_category
  - campi tipici: `id` (PK, UUID memorizzato come stringa), `category_name` (unique), `created_by` (FK → users.email — email string), `created_at` (UTC).
  - scopo: raggruppare prodotti in categorie per filtro e navigazione. Nota: nel modello attuale la colonna che definisce il nome è `category_name` (univoca) e il creatore è referenziato tramite l'email dell'utente (`users.email`).

- tb_product
- tb_product
  - campi tipici: `id` (PK, UUID memorizzato come stringa), `name` (unique), `description` (nullable), `price` (float, non null), `quantity` (int, non null), `category_id` (FK → tb_category.id), `created_by` (FK → users.email — email string), `created_at` (UTC).
  - scopo: rappresentare i prodotti gestiti dal servizio (informazioni, prezzo, quantità e relazioni con categoria e utente). Nota: nel modello attuale il riferimento al creatore (`created_by`) utilizza l'email dell'utente (`users.email`) come chiave esterna anziché l'ID utente.

Ogni modello è una classe SQLAlchemy che definisce colonne, chiavi primarie/esterne e, dove utile, indici. I nomi mostrati sopra sono indicativi e rispecchiano le convenzioni usate nel progetto (prefisso `tb_` per le tabelle).

### Repository

I repository sono classi che incapsulano l'accesso al database e le operazioni CRUD; si trovano in `app/src/core/db/repository` o in file affini. Il loro scopo è isolare la logica di persistenza dalla logica di business (services). Operano su una istanza di `Session` fornita dal layer di database.

Operazioni tipiche fornite dai repository:

#### Operazioni per `tb_user` (UserRepository)

Il repository `UserRepository` (file: `app/src/core/db/repository/tb_user_repository.py`) incapsula le operazioni di accesso e modifica dei record nella tabella `tb_user`. Le operazioni implementate nel file seguono una logica semplice e orientata all'uso pratico: usano l'email come chiave primaria per le ricerche e, nelle operazioni di scrittura, eseguono il commit immediato sulla sessione.

Metodi principali

- get_user_by_email(email: str) -> TbUser | None
  - Recupera il primo utente che corrisponde all'email fornita. Restituisce l'istanza `TbUser` oppure `None` se non esiste.

- create_user(email: str, username: str, hashed_password: str) -> TbUser
  - Crea un nuovo utente con i campi `email`, `username` e `password_hash` (il repository usa `password_hash` come nome del campo nel modello).
  - Aggiunge l'entità alla sessione e chiama `commit()` immediatamente; restituisce l'istanza creata.
  - Nota: non effettua controlli di unicità prima del commit (si può rely sul vincolo DB su `email`), quindi in caso di duplicati si propaga un'eccezione da SQLAlchemy/DB.

- update_user(email: str, fields: dict[str, str]) -> TbUser | None
  - Recupera l'utente per `email`, aggiorna i campi forniti nel dizionario `fields`, effettua `commit()` e restituisce l'utente aggiornato.
  - Se l'utente non esiste, restituisce `None`.

- delete_user(email: str) -> TbUser | None
  - Recupera l'utente per `email`, lo elimina dalla sessione, effettua `commit()` e restituisce l'istanza eliminata.
  - Se l'utente non esiste, restituisce `None`.

Comportamento transazionale

Nel repository le operazioni di scrittura (`create_user`, `update_user`, `delete_user`) eseguono `session.commit()` internamente: questo rende l'uso semplice e immediato ma implica che il controllo della transazione è gestito a livello del repository stesso. In alcuni progetti è preferibile che il repository non esegua il commit ma lasci la responsabilità al chiamante (es. `session_scope()` o a una service function) per poter raggruppare più operazioni in un'unica transazione.

Esempi d'uso

1) Esempio in script o task con `session_scope()` (commit gestito automaticamente dal context manager, ma qui il repository effettuerà comunque commit al suo interno):

```python
from src.core.db.database import session_scope
from src.core.db.repository.tb_user_repository import UserRepository

with session_scope() as session:
    repo = UserRepository(session)
    user = repo.create_user(email="mario@example.com", username="mario", hashed_password="<hash>")
    print("Utente creato:", user.email)
```

2) Esempio in endpoint FastAPI usando la dipendenza `get_db_session`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.db.database import get_db_session
from src.core.db.repository.tb_user_repository import UserRepository

router = APIRouter()

@router.post('/users')
def create_user(payload: dict, db: Session = Depends(get_db_session)):
    repo = UserRepository(db)
    existing = repo.get_user_by_email(payload['email'])
    if existing:
        raise HTTPException(status_code=400, detail='Email già registrata')
    user = repo.create_user(payload['email'], payload.get('username', ''), payload['password_hash'])
    return {"email": user.email}
```

Consigli e possibili miglioramenti

- Se desideri controllare le transazioni a livello superiore (es. per gruppi di operazioni atomiche), sposta i `commit()` fuori dal repository e lascia che il caller gestisca commit/rollback.
- Aggiungi metodi come `get_by_id`, `list` con filtri e paginazione per rendere il repository più completo.
- Gestisci esplicitamente i casi di violazione di unicità (per creare risposte utente-friendly) intercettando l'eccezione del DB al momento del commit.

#### Operazioni per `tb_category` (CategoryRepository)
Il repository `CategoryRepository` (file: `app/src/core/db/repository/tb_category_repository.py`) gestisce l'accesso e le operazioni sulla tabella `tb_category`.

Metodi principali

- get_category_by_name(category_name: str) -> TbCategory | None
  - Recupera una singola categoria corrispondente a `category_name` usando `select(...).where(...)` e `scalar_one_or_none()`.
  - Ritorna l'istanza `TbCategory` se trovata, altrimenti `None`.

- create_category(category_name: str, user_email: str) -> TbCategory
  - Crea una nuova categoria impostando `category_name` e `created_by` (l'email dell'utente che la crea).
  - Aggiunge l'entità alla sessione e chiama `commit()`; restituisce l'istanza appena creata.
  - Nota: non esegue un controllo esplicito di unicità a livello applicativo prima del commit — in caso di duplicato il vincolo DB solleverà un'eccezione.

- get_all_categories() -> list[TbCategory]
  - Recupera tutte le categorie con `select(TbCategory)` e `scalars().all()`.
  - Restituisce una lista (anche vuota) di oggetti `TbCategory`.

- delete_category(category: TbCategory) -> bool
  - Riceve un'istanza `TbCategory`, tenta di eliminarla e fa `commit()`.
  - Ritorna `True` se l'operazione ha successo, `False` in caso di eccezione (il metodo cattura genericamente le eccezioni e ritorna False).

Comportamento transazionale e considerazioni

- Le operazioni di scrittura (`create_category`, `delete_category`) eseguono `session.commit()` internamente, semplificando l'uso ma limitando il controllo delle transazioni a livello superiore.
- `delete_category` cattura qualsiasi eccezione e ritorna `False`; questo è comodo per chiamanti che non vogliono gestire eccezioni, ma può nascondere errori importanti. Considera di lanciare eccezioni specifiche o di loggare l'errore per facilitare il debug.
- `create_category` si affida al vincolo di unicità del DB per evitare duplicati: puoi aggiungere un controllo esplicito con `get_category_by_name` prima di creare la categoria per restituire un messaggio più chiaro all'utente.

Esempi di utilizzo

1) Script o task con `session_scope()`:

```python
from src.core.db.database import session_scope
from src.core.db.repository.tb_category_repository import CategoryRepository

with session_scope() as session:
    repo = CategoryRepository(session)
    cat = repo.create_category('Tazze', user_email='mario@example.com')
    print('Categoria creata:', cat.category_name)
```

2) Endpoint FastAPI (dipendenza `get_db_session`):

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.db.database import get_db_session
from src.core.db.repository.tb_category_repository import CategoryRepository

router = APIRouter()

@router.post('/categories')
def create_category(payload: dict, db: Session = Depends(get_db_session)):
    repo = CategoryRepository(db)
    existing = repo.get_category_by_name(payload['category_name'])
    if existing:
        raise HTTPException(status_code=400, detail='Categoria già esistente')
    cat = repo.create_category(payload['category_name'], payload.get('user_email'))
    return {"category_name": cat.category_name}
```

Consigli e possibili miglioramenti

- Gestione degli errori: intercetta eccezioni specifiche dal DB (es. IntegrityError) e rimappa in errori applicativi significativi.
- Validazione input: assicurati che `category_name` rispetti lunghezza e caratteri consentiti prima di tentare la creazione.
- Transazioni aggregate: se devi creare più entità insieme (es. categoria + prodotti), considera di rimuovere i `commit()` dai repository e farli nel livello service o in un `session_scope()` esterno.
- Soft delete: se vuoi mantenere lo storico, valuta l'introduzione di una colonna `is_deleted` e filtri a livello di repository invece di cancellazioni fisiche.

Se vuoi, posso aggiungere esempi di gestione delle eccezioni (con `IntegrityError`) o un'implementazione alternativa del metodo `delete_category` che lancia eccezioni invece di ritornare un booleano.


#### Operazioni per `tb_product` (ProductRepository)
Il repository `ProductRepository` (file: `app/src/core/db/repository/tb_product_repository.py`) gestisce le operazioni CRUD sulla tabella `tb_product`. Fornisce metodi semplici e pratici per creare, leggere, aggiornare e cancellare prodotti, e ritorna oggetti `TbProduct` o strutture native Python quando appropriato.

Metodi principali

- create_product(name: str, price: float, email: str, quantity: int, description: str | None = None) -> TbProduct
  - Crea un nuovo prodotto con i campi forniti (`name`, `description`, `price`, `quantity`, `created_by` impostato con l'email fornita).
  - Aggiunge l'entità alla sessione e fa `commit()` immediatamente; restituisce l'istanza appena creata.
  - Nota: il repository si affida ai vincoli del DB (es. `name` unique) per gestire duplicati; in caso di violazione verrà sollevata un'eccezione dal DB.

- get_product_by_name(name: str) -> TbProduct | None
  - Recupera un singolo prodotto con il nome dato usando `select(...).where(...)` e `scalar_one_or_none()`.
  - Restituisce l'istanza `TbProduct` se trovata, altrimenti `None`.

- get_all_products() -> list[TbProduct]
  - Recupera tutti i prodotti con `select(TbProduct)` e `scalars().all()`; restituisce una lista di oggetti `TbProduct`.

- update_product(fields: dict[str, Any], product: TbProduct) -> TbProduct
  - Aggiorna i campi dell'istanza `product` con i valori nel dizionario `fields` (controlla `hasattr` prima di settare).
  - Dopo il `commit()` esegue `refresh(product)` per assicurarsi che l'istanza rifletta lo stato corrente del DB e la ritorna.

- delete_product(product: TbProduct) -> bool
  - Tenta di eliminare l'istanza `product` dalla sessione e fa `commit()`.
  - In caso di eccezione esegue `rollback()` e ritorna `False`; altrimenti ritorna `True`.

Comportamento transazionale

- Le operazioni di scrittura eseguono `session.commit()` internamente (semplificando l'uso), ma questo riduce la possibilità di comporre più operazioni in un'unica transazione atomica. Se hai bisogno di transazioni aggregate, valuta di rimuovere i `commit()` dai repository e di gestirli nel livello service o con `session_scope()`.
- `delete_product` esegue rollback in caso di eccezione e ritorna `False`; considera di loggare o rilanciare eccezioni più specifiche se vuoi gestire i failure in modo esplicito.

Esempi d'uso

1) Script / task con `session_scope()`:

```python
from src.core.db.database import session_scope
from src.core.db.repository.tb_product_repository import ProductRepository

with session_scope() as session:
    repo = ProductRepository(session)
    prod = repo.create_product(name='Tazza', price=12.5, email='mario@example.com', quantity=10, description='Tazza in ceramica')
    print('Creato prodotto:', prod.name)
```

2) Endpoint FastAPI con dependency `get_db_session`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.db.database import get_db_session
from src.core.db.repository.tb_product_repository import ProductRepository

router = APIRouter()

@router.post('/products')
def create_product(payload: dict, db: Session = Depends(get_db_session)):
    repo = ProductRepository(db)
    existing = repo.get_product_by_name(payload['name'])
    if existing:
        raise HTTPException(status_code=400, detail='Prodotto con questo nome già esistente')
    prod = repo.create_product(
        name=payload['name'],
        price=payload['price'],
        email=payload.get('created_by', ''),
        quantity=payload.get('quantity', 1),
        description=payload.get('description'),
    )
    return {"name": prod.name, "id": prod.id}
```

Suggerimenti e miglioramenti

- Filtri e paginazione: aggiungi metodi come `list(filters..., limit, offset)` per supportare query paginate e filtri (prezzo min/max, nome contains, categoria, ecc.).
- Gestione errori: intercetta eccezioni specifiche del DB (ad es. `IntegrityError`) per rimappare messaggi più chiari all'utente e gestire il rollback in modo mirato.
- Soft delete: se vuoi preservare lo storico, implementa `is_deleted` e filtri a livello repository invece di cancellazioni fisiche.
- Validazione: valida i campi di input prima della creazione (es. prezzo >= 0, quantity >= 0) nel livello service o nel repository.

## API
La sezione API descrive gli endpoint esposti dal servizio, organizzati in router per versione e risorsa (es. `user_endpoint.py`, `product_endpoint.py`, `category_endpoint.py`). Ogni endpoint segue le convenzioni REST e utilizza le dipendenze per gestire autenticazione, autorizzazione e accesso al database.

### User Endpoint

Questo router si trova in `app/src/routers/v1/user_endpoint.py` e gestisce tutte le operazioni relative agli utenti: registrazione, autenticazione, logout, aggiornamento profilo e cancellazione dell'account. Gli endpoint usano gli schemi definiti in `app/src/schemas` per validare input e output e si appoggiano ai servizi in `app/src/services/users` per la logica di business.

Panoramica degli endpoint

- POST /user/auth/registration
  - Scopo: registrare un nuovo utente.
  - Payload: `UserRegisterRequest` (es. email, username, password).
  - Risposta: `UserRegisterResponse` con i dati dell'utente creato.
  - Codice: 201 Created.

- POST /user/auth/login
  - Scopo: autenticare un utente e rilasciare un access token memorizzato in cookie HTTP-only.
  - Payload: `UserLoginRequest` (email e password).
  - Effetto collaterale: viene impostato un cookie `access_token` con le proprietà definite in `settings.token` (httponly, secure, samesite, max_age).
  - Risposta: `UserLoginResponse` che include i dati dell'utente e metadati sul token.
  - Codice: 200 OK. In caso di credenziali errate viene sollevata `InvalidCredentialsException` (401).

- POST /user/auth/logout
  - Scopo: invalidare la sessione lato client cancellando il cookie `access_token`.
  - Autenticazione: richiede l'utente autenticato tramite la dipendenza `get_current_user`.
  - Risposta: `UserLogoutResponse` (200 OK).

- PATCH /user/profile/update
  - Scopo: aggiornare i dati del profilo dell'utente autenticato (email, password, ecc.).
  - Autenticazione: richiede `get_current_user`.
  - Payload: `UserUpdateRequest`.
  - Comportamento: se l'email viene modificata, il server emette un nuovo token e aggiorna il cookie `access_token` con il nuovo valore.
  - Risposta: `UserUpdateResponse` (200 OK).

- DELETE /user/profile/delete
  - Scopo: cancellare l'account dell'utente autenticato.
  - Autenticazione: richiede `get_current_user`.
  - Effetto collaterale: il cookie `access_token` viene cancellato.
  - Risposta: `UserDeleteResponse` (200 OK) oppure eccezione `UserNotFoundException` (404) se l'utente non esiste.

Autenticazione e comportamento del token

- Il progetto usa token JWT per l'autenticazione; i token vengono generati tramite `create_access_token` e inseriti in un cookie `access_token` con attributo `HttpOnly` per impedire l'accesso tramite JavaScript.
- Le proprietà del cookie (httponly, secure, same_site, durata) sono lette da `settings.token` ed applicate al momento dell'impostazione del cookie.
- L'accesso agli endpoint `profile/*` richiede la dipendenza `get_current_user` che verifica il cookie e valida il token.

Errori e eccezioni

- `InvalidCredentialsException` (401): sollevata quando le credenziali fornite a `/auth/login` non sono corrette.
- `UserNotFoundException` (404): sollevata quando si tenta di cancellare o modificare un utente che non esiste.
- Altre eccezioni di validazione (400) possono essere sollevate dagli schemi Pydantic se il payload non è conforme.

Esempi (curl)

1) Registrazione

```bash
curl -X POST http://localhost:8000/user/auth/registration \
  -H "Content-Type: application/json" \
  -d '{"email":"mario@example.com","username":"mario","password":"Secret123"}'
```

2) Login (ottieni cookie)

```bash
curl -i -X POST http://localhost:8000/user/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mario@example.com","password":"Secret123"}'
```

Nota su sicurezza e deployment

- In ambiente di produzione imposta `settings.token.secure` a True per inviare i cookie solo su connessioni HTTPS.
- Valuta l'uso di SameSite e politiche CORS appropriate se il front-end è servito da un dominio differente.
- Considera la rotazione/regenerazione dei token in caso di cambio email o altre operazioni sensibili.

Se vuoi, posso aggiungere esempi completi con risposte JSON simulative per ogni endpoint, o generare snippet di test (pytest) che verificano il comportamento di registrazione/login/logout usando il client di FastAPI.


### Product Endpoint

Il router per i prodotti si trova in `app/src/routers/v1/product_endpoint.py`. Espone gli endpoint per creare, aggiornare, cancellare e leggere i prodotti. Si appoggia ai servizi in `src.services.products` (es. `product_creation`, `product_to_update`, `product_delete`, `get_all_products`, `get_single_product`) e usa gli schemi Pydantic/Expr (in `src.schemas.product_request` e `src.schemas.product_response`) per validare input e formattare le risposte.

Autenticazione
- Gli endpoint di scrittura (creazione, aggiornamento, cancellazione) richiedono che l'utente sia autenticato: il router usa la dipendenza `get_current_user` per ottenere l'email dell'utente corrente (usata come `created_by` / `product_owner`).
- Gli endpoint di lettura (`/all` e `/{product_name}`) sono pubblici e non richiedono autenticazione.

Elenco degli endpoint

- POST /products/creation
  - Descrizione: crea un nuovo prodotto.
  - Richiede: autenticazione (cookie/token valida tramite `get_current_user`).
  - Payload: `ProductCreationRequest` (es. name, description, price, quantity, category_id).
  - Risposta: `ProductResponse` con i dati del prodotto creato.
  - Codice: 201 Created.

- PATCH /products/update
  - Descrizione: aggiorna un prodotto esistente (i dettagli del prodotto e i campi aggiornabili sono definiti in `ProductUpdateRequest`).
  - Richiede: autenticazione (il `current_user` deve essere il proprietario del prodotto, il controllo è effettuato nel service `product_to_update`).
  - Payload: `ProductUpdateRequest` (es. name, description, price, quantity, id o name per identificare il prodotto).
  - Risposta: `ProductResponse` con i dati aggiornati.
  - Codice: 202 Accepted.

- DELETE /products/delete
  - Descrizione: elimina un prodotto.
  - Richiede: autenticazione (il proprietario della risorsa deve corrispondere a `created_by`).
  - Payload: `ProductDeleteRequest` (es. identificatore del prodotto).
  - Risposta: `ProductDeletionResponse` con lo stato dell'operazione.
  - Codice: 200 OK.

- GET /products/all
  - Descrizione: recupera la lista di tutti i prodotti.
  - Parametri: nessuno (implementazioni successive possono aggiungere query params per filtri/paginazione).
  - Risposta: `ListProductsResponse` con la lista dei prodotti come `ProductResponse`.
  - Codice: 200 OK.

- GET /products/{product_name}
  - Descrizione: recupera un singolo prodotto identificato per nome.
  - Parametri: `product_name` (path parameter).
  - Risposta: `ProductResponse`.
  - Codice: 200 OK oppure 404 Not Found se il prodotto non esiste.

Comportamento e log
- Il router registra eventi significativi (es. creazione/aggiornamento/recupero riuscito) usando `loguru.logger` per facilitare il tracciamento delle operazioni nei log.
- Le validazioni più complesse e i controlli di ownership sono implementati nel livello service (`src.services.products`). Il router rimane uno strato sottile che valida l'input e traduce il risultato in schemi di risposta.

Errori comuni
- 401 Unauthorized: restituito se l'utente non è autenticato quando richiesto.
- 403 Forbidden: restituito se un utente autenticato tenta di modificare o eliminare un prodotto di cui non è il proprietario (gestito nel service).
- 404 Not Found: restituito quando si richiede un prodotto inesistente (`get_single_product`).
- 400 Bad Request: per payload non conformi agli schemi (errori Pydantic).

Esempi (curl)

1) Recuperare tutti i prodotti (pubblico):

```bash
curl -sS http://localhost:8000/products/all
```

2) Creare un prodotto (richiede autenticazione; qui si assume che tu abbia già un cookie `access_token` ottenuto con il login):

```bash
curl -X POST http://localhost:8000/products/creation \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=eyJhbGci..." \
  -d '{"name":"Tazza Bianca","description":"Tazza in ceramica bianca","price":9.9,"quantity":20,"category_id":1}'
```

3) Ottenere un prodotto per nome:

```bash
curl -sS http://localhost:8000/products/Tazza%20Bianca
```

Nota su estensioni future
- Filtri, ricerca full-text, ordinamento e paginazione dovrebbero essere aggiunti a `/products/all` per ridurre il carico e permettere navigazione efficiente.
- Considera l'introduzione di controlli di rate limiting o politiche di caching per le richieste pubbliche più frequenti.

### Category Endpoint
Il router per le categorie si trova in `app/src/routers/v1/category_endpoint.py` e fornisce tre endpoint principali per la gestione delle categorie: creazione, elenco e cancellazione. Il router si appoggia ai servizi in `src.services.products.category_service` e usa gli schemi `CategoryRequest`, `CategoryResponse` e `CategoryDeleteResponse` per input/output.

Endpoint e comportamento

- POST /category/create
  - Scopo: creare una nuova categoria.
  - Autenticazione: richiesta tramite la dipendenza `get_current_user` (il creatore viene registrato come `created_by`).
  - Payload: `CategoryRequest` (campo `name`).
  - Azione: chiama `create_new_category(category_name, user_email)` e ritorna `CategoryResponse` con i dati della categoria creata.
  - Codice HTTP: 201 Created.

- GET /category/list
  - Scopo: restituire l'elenco di tutte le categorie disponibili.
  - Autenticazione: non richiesta (endpoint pubblico).
  - Azione: chiama `get_all_categories()` e mappa i risultati in `CategoryResponse`.
  - Codice HTTP: 200 OK.

- DELETE /category/delete
  - Scopo: cancellare una categoria identificata dal nome.
  - Autenticazione: richiesta tramite `get_current_user`.
  - Payload: `CategoryRequest` (campo `name` che identifica la categoria).
  - Azione: chiama `delete_category(category_name)` e ritorna `CategoryDeleteResponse` con l'esito dell'operazione.
  - Codice HTTP: 200 OK. In caso di problemi (categoria non esistente o vincoli referenziali) il servizio può sollevare eccezioni che mappano in risposte 4xx/5xx.

Log e osservabilità
- Il router usa `loguru.logger` per registrare eventi significativi come la creazione di categorie e la lista delle categorie per facilitare il tracciamento e il debug.

Errori comuni
- 401 Unauthorized: restituito quando si tenta di creare o cancellare una categoria senza autenticazione.
- 404 Not Found o 400 Bad Request: possono essere restituiti dal service se la categoria non esiste o il payload non è valido.

Esempi (curl)

1) Creare una categoria (richiede autenticazione; si assume il cookie `access_token`):

```bash
curl -i -X POST http://localhost:8000/category/create \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=eyJhbGci..." \
  -d '{"name":"Tazze"}'
```

2) Ottenere la lista delle categorie (pubblico):

```bash
curl -sS http://localhost:8000/category/list
```

3) Cancellare una categoria (richiede autenticazione):

```bash
curl -i -X DELETE http://localhost:8000/category/delete \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=eyJhbGci..." \
  -d '{"name":"Tazze"}'
```

Consigli pratici
- Prima di creare una categoria, verifica (opzionalmente) l'esistenza per fornire messaggi user-friendly invece di affidarsi solo al vincolo di unicità del DB.
- Per la cancellazione valuta l'uso di soft delete (`is_deleted`) per mantenere lo storico e prevenire problemi con prodotti già associati.

Vuoi che aggiunga esempi di risposta JSON o test automatici (pytest) per questi endpoint? 
