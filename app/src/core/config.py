# python
import importlib.resources as pkg_resources
import os
from pathlib import Path
from typing import Any, ClassVar, Optional, get_args, get_origin

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VARIABLES_FILE = PROJECT_ROOT / "env" / "local.env"
if Path(VARIABLES_FILE).exists():
    load_dotenv(dotenv_path=VARIABLES_FILE)


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


class Settings(BaseModel):
    logging: LoggingConfig

    # Variabile di classe per mantenere l'istanza singleton
    _instance: ClassVar[Optional["Settings"]] = None

    @classmethod
    def from_yaml_env(cls) -> "Settings":
        # Se l'istanza singleton esiste, ritornala direttamente
        if cls._instance is not None:
            return cls._instance

        try:
            # Use package string to satisfy type checkers
            with pkg_resources.open_text("app.config", "config.yml") as f:
                yaml_config: dict[str, Any] = yaml.safe_load(f) or {}
        except FileNotFoundError as exc:
            raise FileNotFoundError("Configuration file not found") from exc

        def cast_value(raw: str, annotation: Any) -> Any:
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

        missing_env_vars: list[str] = []

        def build_section(
            model_cls: type[BaseModel], yaml_section: Any, path: list[str]
        ) -> dict[str, Any]:
            if yaml_section is None:
                yaml_section = {}

            if not isinstance(yaml_section, dict):
                raise RuntimeError(
                    f"YAML section at path {'.'.join(path)} must be a "
                    f"dictionary, got {type(yaml_section).__name__}"
                )

            result: dict[str, Any] = {}

            for field_name, field_info in model_cls.model_fields.items():
                field_annotation = field_info.annotation
                field_path = path + [field_name]
                env_name = "_".join(p.upper() for p in field_path)

                # Nested BaseModel: build recursively (uses YAML subsection if present)
                if isinstance(field_annotation, type) and issubclass(
                    field_annotation, BaseModel
                ):
                    nested_yaml = yaml_section.get(field_name, {})
                    result[field_name] = build_section(
                        field_annotation, nested_yaml, field_path
                    )
                    continue

                # Environment variable takes precedence
                if env_name in os.environ:
                    raw_value = os.environ[env_name]
                    value = cast_value(raw_value, field_info.annotation)
                    result[field_name] = value
                elif field_name in yaml_section:
                    result[field_name] = yaml_section[field_name]
                else:
                    missing_env_vars.append(env_name)

            return result

        root_dict = build_section(model_cls=Settings, yaml_section=yaml_config, path=[])

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


settings = Settings.from_yaml_env()
