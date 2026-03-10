"""
Modulo di configurazione dell'applicazione.

Carica e valida le impostazioni dell'applicazione combinando un file YAML
(``config/config.yml``) con le variabili d'ambiente. Le variabili d'ambiente
hanno la precedenza sui valori definiti nel file YAML.

Il nome di ogni variabile d'ambiente è costruito concatenando i nomi delle
sezioni annidate in maiuscolo separati da ``_``
(es. ``APP_PORT``, ``DATABASE_HOST``).

All'avvio del modulo viene tentata la creazione di un'istanza singleton
``settings`` di :class:`Settings`. Se il file di configurazione non viene
trovato (ad es. durante l'esecuzione dei test), ``settings`` viene impostato
a ``None``.
"""

import importlib.resources as pkg_resources
import os
from pathlib import Path
from typing import Any, ClassVar, Literal, Optional, get_args, get_origin

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VARIABLES_FILE = PROJECT_ROOT / "env" / "local.env"
if Path(VARIABLES_FILE).exists():
    load_dotenv(dotenv_path=VARIABLES_FILE)


class AppConfig(BaseModel):
    """Configurazione generale dell'applicazione.

    Attributes:
        name: Nome dell'applicazione.
        host: Indirizzo host su cui il server è in ascolto.
        port: Porta su cui il server è in ascolto.
        version: Versione dell'applicazione (es. ``"1.0.0"``).
        environment: Ambiente di esecuzione; può essere ``"dev"`` o ``"prod"``.
        workers: Numero di worker Uvicorn/Gunicorn da avviare.
        debug: Se ``True``, abilita la modalità di debug.
    """

    name: str
    host: str
    port: int
    version: str
    environment: Literal["dev", "prod"]
    workers: int
    debug: bool


class LoggingConfig(BaseModel):
    """Configurazione del sistema di logging (Loguru).

    Attributes:
        level: Livello minimo di log (es. ``"DEBUG"``, ``"INFO"``, ``"ERROR"``).
        json_format: Se ``True``, i log vengono emessi in formato JSON.
        file_enabled: Se ``True``, i log vengono scritti su file.
        file_path: Percorso del file di log.
        rotation: Criterio di rotazione del file di log (es. ``"10 MB"``).
        retention: Durata della retention dei file di log (es. ``"7 days"``).
        backtrace: Se ``True``, include il backtrace completo negli errori.
        diagnose: Se ``True``, aggiunge informazioni diagnostiche agli errori.
        colorize: Se ``True``, colorizza l'output del log su terminale.
        enqueue: Se ``True``, i messaggi di log vengono accodati in modo asincrono.
        service_name: Nome del servizio da includere nei messaggi di log.
    """

    level: str
    json_format: bool
    file_enabled: bool
    file_path: str
    rotation: str
    retention: str
    backtrace: bool
    diagnose: bool
    colorize: bool
    enqueue: bool
    service_name: str


class DatabaseConfig(BaseModel):
    """Configurazione della connessione al database.

    Attributes:
        driver: Driver SQLAlchemy da utilizzare (es. ``"sqlite"``, ``"postgresql"``).
        host: Hostname del server database.
        port: Porta del server database.
        name: Nome del database.
        user: Nome utente per l'autenticazione.
        password: Password per l'autenticazione.
        pool_size: Numero di connessioni mantenute nel pool.
        max_overflow: Connessioni aggiuntive consentite oltre ``pool_size``.
        pool_timeout: Secondi di attesa per ottenere una connessione dal pool.
        pool_recycle: Secondi dopo i quali una connessione viene riciclata.
        pool_pre_ping: Se ``True``, verifica la connessione prima di ogni utilizzo.
    """

    driver: str
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    pool_pre_ping: bool


class TokenConfig(BaseModel):
    secret_key: str
    algorithm: str
    http_only: bool
    secure: bool
    same_site: Literal["lax", "strict", "none"]
    expiration: int


class Settings(BaseModel):
    """Impostazioni globali dell'applicazione (singleton).

    Aggrega :class:`AppConfig`, :class:`LoggingConfig` e :class:`DatabaseConfig`.
    Viene istanziata una sola volta tramite il metodo di fabbrica
    :meth:`from_yaml_env` e l'istanza viene memorizzata in ``_instance``.

    Attributes:
        app: Configurazione dell'applicazione.
        logging: Configurazione del logging.
        database: Configurazione del database.
    """

    app: AppConfig
    logging: LoggingConfig
    database: DatabaseConfig
    token: TokenConfig

    # Variabile di classe per mantenere l'istanza singleton
    _instance: ClassVar[Optional["Settings"]] = None

    @staticmethod
    def _cast_value(raw: str, annotation: Any) -> Any:
        """Converte una stringa nel tipo appropriato basandosi sull'annotazione.

        Supporta i tipi ``bool``, ``int``, ``float`` e ``str``. Gestisce
        correttamente i tipi ``Optional[T]`` estraendo il tipo interno ``T``.

        Args:
            raw: Valore grezzo letto dalla variabile d'ambiente.
            annotation: Tipo atteso (ottenuto dalle annotazioni del modello Pydantic).

        Returns:
            Il valore convertito nel tipo corretto.
        """
        origin = get_origin(annotation)
        args = get_args(annotation)

        # Gestione dei tipi Optional[T]
        if origin is not None and type(None) in args:
            not_none = [arg for arg in args if arg is not type(None)]
            if not_none:
                annotation = not_none[0]

        if annotation is bool:
            return raw.strip().lower() in ["true", "yes", "on", "1", "y"]
        if annotation is int:
            return int(raw)
        if annotation is float:
            return float(raw)
        return raw

    @classmethod
    def _load_yaml_config(cls) -> dict[str, Any]:
        """Carica la configurazione dal file YAML.

        Legge ``config/config.yml`` tramite ``importlib.resources``.

        Returns:
            Dizionario con il contenuto del file YAML, o un dizionario vuoto
            se il file è vuoto.

        Raises:
            FileNotFoundError: Se il file ``config.yml`` non viene trovato.
        """
        try:
            with pkg_resources.open_text("config", "config.yml") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError as exc:
            raise FileNotFoundError("Configuration file not found") from exc

    @classmethod
    def _process_field(
        cls,
        field_name: str,
        field_info: Any,
        yaml_section: dict[str, Any],
        path: list[str],
        missing_env_vars: list[str],
    ) -> tuple[str, Any]:
        """Processa un singolo campo del modello determinandone il valore.

        La priorità di risoluzione è la seguente:

        1. Variabile d'ambiente (nome costruito dal ``path`` corrente).
        2. Valore presente nel file YAML.
        3. Se nessuna delle precedenti è disponibile, il nome della variabile
           d'ambiente mancante viene aggiunto a ``missing_env_vars``.

        Se il campo è a sua volta un :class:`~pydantic.BaseModel`, la
        costruzione avviene ricorsivamente tramite :meth:`_build_section`.

        Args:
            field_name: Nome del campo del modello Pydantic.
            field_info: Oggetto ``FieldInfo`` di Pydantic che descrive il campo.
            yaml_section: Dizionario con i valori YAML della sezione corrente.
            path: Lista dei nomi di sezione che compongono il percorso corrente
                (usata per costruire il nome della variabile d'ambiente).
            missing_env_vars: Lista accumulatrice dei nomi delle variabili
                d'ambiente mancanti.

        Returns:
            Una tupla ``(field_name, value)`` con il nome del campo e il valore
            risolto (o ``None`` se mancante).
        """
        field_annotation = field_info.annotation
        field_path = path + [field_name]
        env_name = "_".join(p.upper() for p in field_path)

        # Nested BaseModel: build recursively
        if isinstance(field_annotation, type) and issubclass(
            field_annotation, BaseModel
        ):
            nested_yaml = yaml_section.get(field_name, {})
            value = cls._build_section(
                field_annotation, nested_yaml, field_path, missing_env_vars
            )
            return field_name, value

        # Environment variable takes precedence
        if env_name in os.environ:
            raw_value = os.environ[env_name]
            value = cls._cast_value(raw_value, field_info.annotation)
            return field_name, value

        # Fallback to YAML value
        if field_name in yaml_section:
            return field_name, yaml_section[field_name]

        # Missing value
        missing_env_vars.append(env_name)
        return field_name, None

    @classmethod
    def _build_section(
        cls,
        model_cls: type[BaseModel],
        yaml_section: Any,
        path: list[str],
        missing_env_vars: list[str],
    ) -> dict[str, Any]:
        """Costruisce ricorsivamente il dizionario dei valori
            per una sezione del modello.

        Itera su tutti i campi di ``model_cls`` e delega la risoluzione del
        singolo valore a :meth:`_process_field`.

        Args:
            model_cls: Classe Pydantic di cui costruire la sezione.
            yaml_section: Dizionario con i valori YAML della sezione corrente,
                oppure ``None`` (verrà trattato come dizionario vuoto).
            path: Lista dei nomi di sezione che compongono il percorso corrente.
            missing_env_vars: Lista accumulatrice dei nomi delle variabili
                d'ambiente mancanti.

        Returns:
            Dizionario ``{field_name: value}`` pronto per essere passato al
            costruttore di ``model_cls``.

        Raises:
            RuntimeError: Se ``yaml_section`` non è un dizionario.
        """
        if yaml_section is None:
            yaml_section = {}

        if not isinstance(yaml_section, dict):
            raise RuntimeError(
                f"YAML section at path {'.'.join(path)} must be a "
                f"dictionary, got {type(yaml_section).__name__}"
            )

        result: dict[str, Any] = {}
        for field_name, field_info in model_cls.model_fields.items():
            key, value = cls._process_field(
                field_name, field_info, yaml_section, path, missing_env_vars
            )
            if value is not None or key not in result:
                result[key] = value

        return result

    @classmethod
    def from_yaml_env(cls) -> "Settings":
        """Carica le impostazioni da YAML e variabili d'ambiente (pattern Singleton).

        Se l'istanza singleton è già stata creata, la restituisce direttamente
        senza rileggere i file di configurazione.

        Returns:
            L'istanza singleton di :class:`Settings`.

        Raises:
            FileNotFoundError: Se il file ``config.yml`` non viene trovato.
            RuntimeError: Se mancano variabili d'ambiente obbligatorie o se
                il parsing della configurazione fallisce.
        """
        # Se l'istanza singleton esiste, ritornala direttamente
        if cls._instance is not None:
            return cls._instance

        yaml_config = cls._load_yaml_config()
        missing_env_vars: list[str] = []
        root_dict = cls._build_section(
            model_cls=Settings,
            yaml_section=yaml_config,
            path=[],
            missing_env_vars=missing_env_vars,
        )

        if missing_env_vars:
            unique_missing = sorted(set(missing_env_vars))
            missing_list = ", ".join(unique_missing)
            raise RuntimeError(
                f"Missing required environment variables: {missing_list}"
            )

        try:
            # Crea l'istanza e la memorizza come singleton
            instance = cls(**root_dict)
            cls._instance = instance
            return instance
        except Exception as exc:
            raise RuntimeError("Failed to parse configuration") from exc


# Initialize settings if not in test mode
try:
    settings = Settings.from_yaml_env()
except (FileNotFoundError, ModuleNotFoundError):
    # Allow import in test mode without actual config file
    settings = None  # type: ignore[assignment]
