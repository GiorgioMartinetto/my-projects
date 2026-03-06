from src.core.db.database import session_scope
from src.core.db.model.tb_user import TbUser
from src.core.db.repository.tb_user_repository import UserRepository
from src.core.security import hash_password

from src.exceptions.user_exception import EmailAlreadyExistsException
from src.routers.v1.user_endpoint import UserRegisterRequest
from src.schemas.user_response import UserRegisterResponse

from loguru import logger
async def _safe_existing_user(email: str) -> bool:
    """
    Verifica se un utente con l'email specificata esiste già nel database.

    Args:
        email (str): L'indirizzo email da verificare.

    Returns:
        bool: True se l'utente esiste, False altrimenti.

    Note:
        Questa funzione utilizza una sessione database sicura tramite session_scope
        per garantire la corretta gestione delle transazioni.
    """
    with session_scope() as session:
        repo = UserRepository(session)
        exists = await repo.get_user_by_email(email=email) is not None

    return exists


async def _safe_create_user(email: str, username: str, password: str) -> TbUser:
    """
    Crea un nuovo utente nel database con i dati specificati.

    Args:
        email (str): L'indirizzo email dell'utente.
        username (str): Il nome utente.
        password (str): La password hashata dell'utente.

    Returns:
        TbUser: L'oggetto utente appena creato.

    Note:
        Questa funzione utilizza una sessione database sicura tramite session_scope
        per garantire la corretta gestione delle transazioni.
    """
    with session_scope() as session:
        repo = UserRepository(session)
        new_user = await repo.create_user(
            email=email,
            username=username,
            hashed_password=password,
        )
        return new_user


async def register_user(payload: UserRegisterRequest) -> UserRegisterResponse:
    """
    Registra un nuovo utente nel sistema.

    Questa funzione gestisce il processo completo di registrazione utente:
    1. Verifica che l'email non sia già registrata
    2. Effettua l'hashing della password
    3. Crea l'utente nel database
    4. Restituisce una risposta di conferma

    Args:
        payload (UserRegisterRequest): I dati di registrazione dell'utente contenenti
            email, nome e password.

    Returns:
        UserRegisterResponse: La risposta contenente un messaggio di conferma e
            i dati dell'utente registrato.

    Raises:
        EmailAlreadyExistsException: Se l'email è già presente nel database.

    Note:
        La password viene automaticamente hashata prima di essere salvata nel database
        per garantire la sicurezza.
    """
    existing = await _safe_existing_user(email=payload.email)
    if existing:
        raise EmailAlreadyExistsException(
            message=f"Email {payload.email} already exists.",
            context={"email": payload.email},
        )
    hashed_password = hash_password(payload.password)

    new_user = await _safe_create_user(
        email = payload.email,
        username = payload.name,
        password = hashed_password
    )

    return UserRegisterResponse.model_validate(
        {
            "message": "User registered successfully.",
            "user": new_user,
        }
    )

