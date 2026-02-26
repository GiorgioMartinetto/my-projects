# python
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
    name: str
    host: str
    port: int
    version: str
    environment: Literal["dev", "prod"]
    workers: int
    debug: bool


class LoggingConfig(BaseModel):
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


class Settings(BaseModel):
    app: AppConfig
    logging: LoggingConfig

    # Variabile di classe per mantenere l'istanza singleton
    _instance: ClassVar[Optional["Settings"]] = None

    @staticmethod
    def _cast_value(raw: str, annotation: Any) -> Any:
        """Converte una stringa nel tipo appropriato basandosi sull'annotazione."""
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
        """Carica la configurazione dal file YAML."""
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
        """Processa un singolo campo del modello."""
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
        """Costruisce ricorsivamente una sezione del modello."""
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
        """Carica le impostazioni da YAML e variabili d'ambiente."""
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
