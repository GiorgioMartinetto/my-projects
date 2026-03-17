from typing import Any

from src.core.db.database import session_scope
from src.core.db.model.tb_user import TbUser
from src.core.db.repository.tb_user_repository import UserRepository
from src.core.security import hash_password, verify_password
from src.exceptions.user_exception import (
    EmailAlreadyExistsException,
    NewPasswordAndOldPasswordNotMatchException,
    PasswordAndConfirmPasswordNotMatchException,
)
from src.schemas.user_request import UserRegisterRequest, UserUpdateRequest
from src.schemas.user_response import (
    UserDeleteResponse,
    UserLoginResponse,
    UserRegisterResponse,
)
from starlette import status


def _safe_existing_user(email: str) -> bool:
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
        exists = repo.get_user_by_email(email=email) is not None

    return exists


def _safe_create_user(email: str, username: str, password: str) -> TbUser:
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
        new_user = repo.create_user(
            email=email,
            username=username,
            hashed_password=password,
        )
        return new_user


def _safe_authenticate_user(email: str, password: str) -> TbUser | None:
    """
    Autentica un utente verificando che la password fornita
    corrisponda a quella salvata.

    Args:
        email (str): L'indirizzo email utilizzato per identificare l'utente.
        password (str): La password in chiaro fornita dall'utente.

    Returns:
        TbUser | None: L'utente autenticato scollegato dalla sessione
                        oppure None se le credenziali non sono valide.

    Note:
        L'oggetto restituito contiene solo i campi essenziali e
        non è legato alla sessione del database.
    """
    with session_scope() as session:
        repo = UserRepository(session)
        user = repo.get_user_by_email(email=email)
        if not user:
            return None
        password_str = str(user.password_hash)

        if not verify_password(
            plain_password=password,
            hashed_password=password_str,
        ):
            return None

        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
        }
    detached_user = TbUser(**user_data)
    return detached_user


def _safe_update_user(user_email: str, fields: dict[str, str]) -> TbUser | None:
    """
    Aggiorna in sicurezza i campi consentiti per l'utente specificato,
    gestendo anche il cambio password.

    Args:
        fields (dict[str, str]): I campi da aggiornare e i valori associati.
        user_email (str): L'indirizzo email dell'utente da modificare.

    Returns:
        TbUser | None: L'utente aggiornato oppure None se non è stato
                        trovato alcun record.

    Raises:
        NewPasswordAndOldPasswordNotMatchException: Se la password
        corrente non corrisponde a quella fornita.
    """
    with session_scope() as session:
        repo = UserRepository(session)
        current_user = repo.get_user_by_email(email=user_email)
        if current_user and "new_password" in fields:
            check_password = verify_password(
                plain_password=fields.get("old_password", ""),
                hashed_password=str(current_user.password_hash),
            )

            if not check_password:
                raise NewPasswordAndOldPasswordNotMatchException(
                    message="Password and confirm password do not match.",
                    context={"email": user_email},
                    status_code=status.HTTP_409_CONFLICT,
                )
            fields.pop("old_password", None)
            fields["password_hash"] = hash_password(fields.pop("new_password", ""))

        updated_user = repo.update_user(
            email=user_email,
            fields=fields,
        )
        return updated_user


def _safe_delete_user(email: str) -> TbUser | None:
    """
    Elimina un utente dal database all'interno di una sessione transazionale sicura.

    Args:
        email (str): L'indirizzo email dell'utente da cancellare.

    Returns:
        TbUser | None: L'utente eliminato oppure None se l'email non esiste.
    """
    with session_scope() as session:
        repo = UserRepository(session)
        deleted_user = repo.delete_user(email=email)

        return deleted_user


def register_user(payload: UserRegisterRequest) -> UserRegisterResponse:
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
    existing = _safe_existing_user(email=payload.email)
    if existing:
        raise EmailAlreadyExistsException(
            message=f"Email {payload.email} already exists.",
            context={"email": payload.email},
        )

    if payload.password != payload.confirm_password:
        raise PasswordAndConfirmPasswordNotMatchException(
            message="Password and confirm password do not match.",
            context={"email": payload.email},
        )

    hashed_password = hash_password(payload.password)

    new_user = _safe_create_user(
        email=payload.email, username=payload.name, password=hashed_password
    )

    return UserRegisterResponse.model_validate(
        {
            "message": "User registered successfully.",
            "user": new_user,
        }
    )


def authenticate_user(email: str, password: str) -> UserLoginResponse | None:
    """
    Gestisce il flusso di autenticazione applicativo
    restituendo la risposta serializzata.

    Args:
        email (str): L'indirizzo email fornito in fase di login.
        password (str): La password in chiaro inserita dall'utente.

    Returns:
        UserLoginResponse | None: La risposta di successo
        se le credenziali sono valide, altrimenti None.
    """
    user = _safe_authenticate_user(email=email, password=password)

    if not user:
        return None

    return UserLoginResponse.model_validate(
        {
            "message": "User authenticated successfully.",
            "email": email,
        }
    )


def update_user_data(
    user_to_update: UserUpdateRequest, current_user: dict[str, Any]
) -> TbUser | None:
    """
    Aggiorna i dati dell'utente autenticato in base ai campi forniti nella richiesta.

    Args:
        user_to_update (UserUpdateRequest): Il payload contenente i campi modificabili.
        current_user (dict): Le informazioni dell'utente autenticato ottenute dal token.

    Returns:
        TbUser | None: L'utente aggiornato oppure None se non è stato trovato.
    """
    user_email = current_user.get("email", None)
    if not isinstance(user_email, str):
        return None
    user_fields: dict[str, str] = {
        field: value
        for field, value in user_to_update.model_dump().items()
        if value is not None
    }

    if not user_fields:
        return None

    user_updated = _safe_update_user(user_email=user_email, fields=user_fields)

    return user_updated


def user_deletion(user_email: str) -> UserDeleteResponse | None:
    """
    Cancella l'utente indicato e costruisce la risposta API coerente
    con l'esito dell'operazione.

    Args:
        user_email (str): L'indirizzo email dell'utente da eliminare.

    Returns:
        UserDeleteResponse | None: La risposta di conferma se
        l'eliminazione va a buon fine, altrimenti None.
    """
    user_deleted = _safe_delete_user(email=user_email)
    if user_deleted:
        return UserDeleteResponse.model_validate(
            {
                "message": "User deleted successfully.",
                "email": user_deleted.email,
            }
        )
    return None
