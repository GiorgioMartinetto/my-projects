"""Test suite for configuration module.

Tests cover:
- Valid configuration loading
- Missing required fields
- Invalid data types
- Invalid literal values
- Environment variable overrides
- Singleton pattern behavior
- None values handling
"""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import mock_open, patch

import pytest
import yaml
from pydantic import ValidationError

from app.src.core.config import AppConfig, DatabaseConfig, LoggingConfig, Settings

# Path to test configuration files
TEST_CONFIG_DIR = Path(__file__).parent / "config_test"


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clean environment variables before and after each test."""
    # Store original env vars
    original_env = os.environ.copy()

    # Remove all APP_, LOGGING_, and DATABASE_ env vars
    keys_to_remove = [
        key for key in os.environ.keys()
        if key.startswith(("APP_", "LOGGING_", "DATABASE_"))
    ]
    for key in keys_to_remove:
        del os.environ[key]

    # Reset singleton
    Settings._instance = None

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

    # Reset singleton again
    Settings._instance = None


@pytest.fixture
def valid_yaml_config() -> dict[str, Any]:
    """Return a valid configuration dictionary."""
    return {
        "app": {
            "name": "Test App",
            "host": "127.0.0.1",
            "port": 9000,
            "version": "2.0.0",
            "environment": "prod",
            "workers": 4,
            "debug": True,
        },
        "logging": {
            "level": "DEBUG",
            "json_format": True,
            "file_enabled": True,
            "file_path": "logs/test.log",
            "rotation": "5 MB",
            "retention": "3 days",
            "backtrace": False,
            "diagnose": False,
            "colorize": True,
            "enqueue": True,
            "service_name": "test-service",
        },
        "database": {
            "driver": "postgresql",
            "host": "db.test.com",
            "port": 5432,
            "name": "testdb",
            "user": "testuser",
            "password": "not_a_real_password",
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 60,
            "pool_recycle": 7200,
            "pool_pre_ping": True,
        },
    }


class TestAppConfig:
    """Test AppConfig model."""

    def test_valid_app_config(self) -> None:
        """Test creating AppConfig with valid data."""
        config = AppConfig(
            name="Test App",
            host="localhost",
            port=8080,
            version="1.0.0",
            environment="dev",
            workers=1,
            debug=False,
        )
        assert config.name == "Test App"
        assert config.host == "localhost"
        assert config.port == 8080
        assert config.version == "1.0.0"
        assert config.environment == "dev"
        assert config.workers == 1
        assert config.debug is False

    def test_invalid_environment_literal(self) -> None:
        """Test that invalid environment value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(
                name="Test App",
                host="localhost",
                port=8080,
                version="1.0.0",
                environment="staging",  # type: ignore[arg-type]
                workers=1,
                debug=False,
            )
        assert "environment" in str(exc_info.value).lower()

    def test_invalid_port_type(self) -> None:
        """Test that invalid port type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(
                name="Test App",
                host="localhost",
                port="not_a_number",  # type: ignore
                version="1.0.0",
                environment="dev",
                workers=1,
                debug=False,
            )
        assert "port" in str(exc_info.value).lower()

    def test_missing_required_field(self) -> None:
        """Test that missing required field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(
                name="Test App",
                host="localhost",
                # port is missing
                version="1.0.0",
                environment="dev",
                workers=1,
                debug=False,
            )  # type: ignore
        assert "port" in str(exc_info.value).lower()


class TestLoggingConfig:
    """Test LoggingConfig model."""

    def test_valid_logging_config(self) -> None:
        """Test creating LoggingConfig with valid data."""
        config = LoggingConfig(
            level="INFO",
            json_format=False,
            file_enabled=True,
            file_path="logs/app.log",
            rotation="10 MB",
            retention="7 days",
            backtrace=True,
            diagnose=False,
            colorize=True,
            enqueue=False,
            service_name="test-service",
        )
        assert config.level == "INFO"
        assert config.json_format is False
        assert config.file_enabled is True
        assert config.file_path == "logs/app.log"

    def test_invalid_boolean_type(self) -> None:
        """Test that invalid boolean type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(
                level="INFO",
                json_format="not_a_bool",  # type: ignore
                file_enabled=True,
                file_path="logs/app.log",
                rotation="10 MB",
                retention="7 days",
                backtrace=True,
                diagnose=False,
                colorize=True,
                enqueue=False,
                service_name="test-service",
            )
        assert "json_format" in str(exc_info.value).lower()

    def test_missing_multiple_fields(self) -> None:
        """Test that missing multiple fields raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(
                level="INFO",
                # Missing several required fields
                file_path="logs/app.log",
            )  # type: ignore
        errors_str = str(exc_info.value).lower()
        assert any(
            field in errors_str for field in ["json_format", "file_enabled", "rotation"]
        )


class TestDatabaseConfig:
    """Test DatabaseConfig model."""

    def test_valid_database_config(self) -> None:
        """Test creating DatabaseConfig with valid data."""
        config = DatabaseConfig(
            driver="postgresql",
            host="localhost",
            port=5432,
            name="mydb",
            user="dbuser",
            password="not_a_real_password",
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )
        assert config.driver == "postgresql"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "mydb"
        assert config.user == "dbuser"
        assert config.password == "not_a_real_password"
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.pool_pre_ping is True

    def test_invalid_port_type(self) -> None:
        """Test that invalid port type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                driver="postgresql",
                host="localhost",
                port="not_a_number",  # type: ignore
                name="mydb",
                user="dbuser",
                password="not_a_real_password",
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
            )
        assert "port" in str(exc_info.value).lower()

    def test_invalid_pool_size_type(self) -> None:
        """Test that invalid pool_size type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                driver="postgresql",
                host="localhost",
                port=5432,
                name="mydb",
                user="dbuser",
                password="not_a_real_password",
                pool_size="invalid",  # type: ignore
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
            )
        assert "pool_size" in str(exc_info.value).lower()

    def test_invalid_pool_pre_ping_type(self) -> None:
        """Test that invalid pool_pre_ping type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                driver="postgresql",
                host="localhost",
                port=5432,
                name="mydb",
                user="dbuser",
                password="not_a_real_password",
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping="not_a_bool",  # type: ignore
            )
        assert "pool_pre_ping" in str(exc_info.value).lower()

    def test_missing_required_field(self) -> None:
        """Test that missing required field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                driver="postgresql",
                host="localhost",
                # port is missing
                name="mydb",
                user="dbuser",
                password="not_a_real_password",
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
            )  # type: ignore
        assert "port" in str(exc_info.value).lower()

    def test_missing_multiple_fields(self) -> None:
        """Test that missing multiple fields raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                driver="postgresql",
                host="localhost",
                # Missing several required fields
                name="mydb",
            )  # type: ignore
        errors_str = str(exc_info.value).lower()
        assert any(
            field in errors_str
            for field in ["port", "user", "password", "pool_size"]
        )


class TestSettings:
    """Test Settings class and from_yaml_env method."""

    def test_valid_configuration_from_yaml(
        self, clean_env: None, valid_yaml_config: dict[str, Any]
    ) -> None:
        """Test loading valid configuration from YAML."""
        yaml_content = yaml.dump(valid_yaml_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            settings = Settings.from_yaml_env()

            assert settings.app.name == "Test App"
            assert settings.app.host == "127.0.0.1"
            assert settings.app.port == 9000
            assert settings.app.environment == "prod"
            assert settings.logging.level == "DEBUG"
            assert settings.logging.json_format is True
            assert settings.database.driver == "postgresql"
            assert settings.database.host == "db.test.com"
            assert settings.database.port == 5432
            assert settings.database.name == "testdb"
            assert settings.database.user == "testuser"
            assert settings.database.password == "not_a_real_password"
            assert settings.database.pool_size == 10
            assert settings.database.max_overflow == 20

    def test_environment_variable_override(
        self, clean_env: None, valid_yaml_config: dict[str, Any]
    ) -> None:
        """Test that environment variables override YAML values."""
        os.environ["APP_PORT"] = "7777"
        os.environ["APP_DEBUG"] = "true"
        os.environ["LOGGING_LEVEL"] = "ERROR"
        os.environ["DATABASE_PORT"] = "3306"
        os.environ["DATABASE_POOL_SIZE"] = "15"

        yaml_content = yaml.dump(valid_yaml_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            settings = Settings.from_yaml_env()

            # Check env vars override YAML
            assert settings.app.port == 7777
            assert settings.app.debug is True
            assert settings.logging.level == "ERROR"
            assert settings.database.port == 3306
            assert settings.database.pool_size == 15

            # Check YAML values still present for non-overridden fields
            assert settings.app.name == "Test App"
            assert settings.app.host == "127.0.0.1"
            assert settings.database.driver == "postgresql"
            assert settings.database.host == "db.test.com"

    def test_boolean_environment_variable_parsing(
        self, clean_env: None, valid_yaml_config: dict[str, Any]
    ) -> None:
        """Test parsing boolean values from environment variables."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("yes", True),
            ("YES", True),
            ("on", True),
            ("1", True),
            ("y", True),
            ("false", False),
            ("False", False),
            ("no", False),
            ("0", False),
            ("off", False),
        ]

        for env_value, expected in test_cases:
            os.environ["APP_DEBUG"] = env_value
            Settings._instance = None  # Reset singleton

            yaml_content = yaml.dump(valid_yaml_config)

            with patch(
                "importlib.resources.open_text", mock_open(read_data=yaml_content)
            ):
                settings = Settings.from_yaml_env()
                assert settings.app.debug is expected, f"Failed for value: {env_value}"

    def test_integer_environment_variable_parsing(
        self, clean_env: None, valid_yaml_config: dict[str, Any]
    ) -> None:
        """Test parsing integer values from environment variables."""
        os.environ["APP_PORT"] = "12345"
        os.environ["APP_WORKERS"] = "8"

        yaml_content = yaml.dump(valid_yaml_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            settings = Settings.from_yaml_env()

            assert settings.app.port == 12345
            assert settings.app.workers == 8

    def test_missing_required_fields(self, clean_env: None) -> None:
        """Test that missing required fields raises RuntimeError."""
        incomplete_config = {
            "app": {
                "name": "Test App",
                "host": "127.0.0.1",
                # port is missing
                "version": "1.0.0",
                "environment": "dev",
                "workers": 1,
                "debug": False,
            },
            "logging": {
                "level": "INFO",
                # json_format is missing
                "file_enabled": False,
                "file_path": "logs/app.log",
                "rotation": "10 MB",
                "retention": "7 days",
                "backtrace": True,
                "diagnose": True,
                "colorize": False,
                "enqueue": False,
                "service_name": "test-service",
            },
        }

        yaml_content = yaml.dump(incomplete_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            with pytest.raises(RuntimeError) as exc_info:
                Settings.from_yaml_env()

            error_msg = str(exc_info.value).lower()
            assert "missing" in error_msg
            assert any(var in error_msg for var in ["app_port", "logging_json_format"])

    def test_invalid_yaml_type(self, clean_env: None) -> None:
        """Test that invalid YAML type in config raises RuntimeError."""
        invalid_config = {
            "app": {
                "name": "Test App",
                "host": "127.0.0.1",
                "port": "not_a_number",  # Invalid type
                "version": "1.0.0",
                "environment": "dev",
                "workers": 1,
                "debug": False,
            },
            "logging": {
                "level": "INFO",
                "json_format": False,
                "file_enabled": False,
                "file_path": "logs/app.log",
                "rotation": "10 MB",
                "retention": "7 days",
                "backtrace": True,
                "diagnose": True,
                "colorize": False,
                "enqueue": False,
                "service_name": "test-service",
            },
            "database": {
                "driver": "postgresql",
                "host": "localhost",
                "port": 5432,
                "name": "testdb",
                "user": "testuser",
                "password": "not_a_real_password",
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True,
            },
        }

        yaml_content = yaml.dump(invalid_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            with pytest.raises(RuntimeError) as exc_info:
                Settings.from_yaml_env()

            assert "failed to parse" in str(exc_info.value).lower()

    def test_invalid_literal_value(self, clean_env: None) -> None:
        """Test that invalid literal value raises RuntimeError."""
        invalid_config = {
            "app": {
                "name": "Test App",
                "host": "127.0.0.1",
                "port": 8080,
                "version": "1.0.0",
                "environment": "staging",  # Invalid literal (should be dev or prod)
                "workers": 1,
                "debug": False,
            },
            "logging": {
                "level": "INFO",
                "json_format": False,
                "file_enabled": False,
                "file_path": "logs/app.log",
                "rotation": "10 MB",
                "retention": "7 days",
                "backtrace": True,
                "diagnose": True,
                "colorize": False,
                "enqueue": False,
                "service_name": "test-service",
            },
            "database": {
                "driver": "postgresql",
                "host": "localhost",
                "port": 5432,
                "name": "testdb",
                "user": "testuser",
                "password": "not_a_real_password",
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True,
            },
        }

        yaml_content = yaml.dump(invalid_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            with pytest.raises(RuntimeError) as exc_info:
                Settings.from_yaml_env()

            assert "failed to parse" in str(exc_info.value).lower()

    def test_empty_yaml_config(self, clean_env: None) -> None:
        """Test that empty YAML config raises RuntimeError for missing fields."""
        yaml_content = ""

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            with pytest.raises(RuntimeError) as exc_info:
                Settings.from_yaml_env()

            assert "missing" in str(exc_info.value).lower()

    def test_singleton_pattern(
        self, clean_env: None, valid_yaml_config: dict[str, Any]
    ) -> None:
        """Test that Settings implements singleton pattern correctly."""
        yaml_content = yaml.dump(valid_yaml_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            settings1 = Settings.from_yaml_env()
            settings2 = Settings.from_yaml_env()

            # Should return the same instance
            assert settings1 is settings2

            # Verify it's actually the same object
            assert id(settings1) == id(settings2)

    def test_config_file_not_found(self, clean_env: None) -> None:
        """Test that missing config file raises FileNotFoundError."""
        with patch(
            "importlib.resources.open_text", side_effect=FileNotFoundError("Not found")
        ):
            with pytest.raises(FileNotFoundError) as exc_info:
                Settings.from_yaml_env()

            assert "configuration file not found" in str(exc_info.value).lower()

    def test_yaml_section_not_dict(self, clean_env: None) -> None:
        """Test that non-dict YAML section raises RuntimeError."""
        invalid_config = {
            "app": "not_a_dict",  # Should be a dict
            "logging": {
                "level": "INFO",
                "json_format": False,
                "file_enabled": False,
                "file_path": "logs/app.log",
                "rotation": "10 MB",
                "retention": "7 days",
                "backtrace": True,
                "diagnose": True,
                "colorize": False,
                "enqueue": False,
                "service_name": "test-service",
            },
        }

        yaml_content = yaml.dump(invalid_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            with pytest.raises(RuntimeError) as exc_info:
                Settings.from_yaml_env()

            error_msg = str(exc_info.value).lower()
            assert "must be a dictionary" in error_msg

    def test_none_values_in_yaml(self, clean_env: None) -> None:
        """Test handling of None values in YAML config."""
        config_with_none = {
            "app": {
                "name": "Test App",
                "host": "127.0.0.1",
                "port": None,  # None value
                "version": "1.0.0",
                "environment": "dev",
                "workers": 1,
                "debug": False,
            },
            "logging": {
                "level": "INFO",
                "json_format": False,
                "file_enabled": False,
                "file_path": "logs/app.log",
                "rotation": "10 MB",
                "retention": "7 days",
                "backtrace": True,
                "diagnose": True,
                "colorize": False,
                "enqueue": False,
                "service_name": "test-service",
            },
            "database": {
                "driver": "postgresql",
                "host": "localhost",
                "port": 5432,
                "name": "testdb",
                "user": "testuser",
                "password": "not_a_real_password",
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True,
            },
        }

        yaml_content = yaml.dump(config_with_none)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            # Should raise error because port is required and None is not valid
            with pytest.raises(RuntimeError):
                Settings.from_yaml_env()

    def test_environment_variable_invalid_int(
        self, clean_env: None, valid_yaml_config: dict[str, Any]
    ) -> None:
        """Test that invalid integer in env var raises ValueError."""
        os.environ["APP_PORT"] = "not_a_number"

        yaml_content = yaml.dump(valid_yaml_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            with pytest.raises(ValueError):
                Settings.from_yaml_env()

    def test_mixed_yaml_and_env_complete_config(self, clean_env: None) -> None:
        """Test loading config with some values from YAML and some from env."""
        partial_yaml_config = {
            "app": {
                "name": "Partial App",
                "host": "localhost",
                # port will come from env
                "version": "1.0.0",
                "environment": "dev",
                # workers will come from env
                "debug": False,
            },
            "logging": {
                # level will come from env
                "json_format": False,
                "file_enabled": False,
                "file_path": "logs/app.log",
                "rotation": "10 MB",
                "retention": "7 days",
                "backtrace": True,
                "diagnose": True,
                "colorize": False,
                "enqueue": False,
                "service_name": "partial-service",
            },
            "database": {
                "driver": "postgresql",
                "host": "partial.db.com",
                # port will come from env
                "name": "partialdb",
                "user": "partialuser",
                "password": "not_a_real_password",
                # pool_size will come from env
                "max_overflow": 15,
                "pool_timeout": 45,
                "pool_recycle": 5400,
                "pool_pre_ping": True,
            },
        }

        # Set missing fields via environment
        os.environ["APP_PORT"] = "5000"
        os.environ["APP_WORKERS"] = "2"
        os.environ["LOGGING_LEVEL"] = "WARNING"
        os.environ["DATABASE_PORT"] = "5433"
        os.environ["DATABASE_POOL_SIZE"] = "8"

        yaml_content = yaml.dump(partial_yaml_config)

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            settings = Settings.from_yaml_env()

            # Check YAML values
            assert settings.app.name == "Partial App"
            assert settings.app.host == "localhost"
            assert settings.app.debug is False
            assert settings.database.driver == "postgresql"
            assert settings.database.host == "partial.db.com"
            assert settings.database.name == "partialdb"

            # Check env values
            assert settings.app.port == 5000
            assert settings.app.workers == 2
            assert settings.logging.level == "WARNING"
            assert settings.database.port == 5433
            assert settings.database.pool_size == 8

    def test_all_values_from_environment(self, clean_env: None) -> None:
        """Test loading all config values from environment variables."""
        # Set all required environment variables
        os.environ["APP_NAME"] = "Env App"
        os.environ["APP_HOST"] = "0.0.0.0"
        os.environ["APP_PORT"] = "3000"
        os.environ["APP_VERSION"] = "3.0.0"
        os.environ["APP_ENVIRONMENT"] = "prod"
        os.environ["APP_WORKERS"] = "10"
        os.environ["APP_DEBUG"] = "false"

        os.environ["LOGGING_LEVEL"] = "CRITICAL"
        os.environ["LOGGING_JSON_FORMAT"] = "true"
        os.environ["LOGGING_FILE_ENABLED"] = "true"
        os.environ["LOGGING_FILE_PATH"] = "logs/env.log"
        os.environ["LOGGING_ROTATION"] = "20 MB"
        os.environ["LOGGING_RETENTION"] = "30 days"
        os.environ["LOGGING_BACKTRACE"] = "false"
        os.environ["LOGGING_DIAGNOSE"] = "false"
        os.environ["LOGGING_COLORIZE"] = "true"
        os.environ["LOGGING_ENQUEUE"] = "true"
        os.environ["LOGGING_SERVICE_NAME"] = "env-service"

        os.environ["DATABASE_DRIVER"] = "mysql"
        os.environ["DATABASE_HOST"] = "db.example.com"
        os.environ["DATABASE_PORT"] = "3306"
        os.environ["DATABASE_NAME"] = "envdb"
        os.environ["DATABASE_USER"] = "envuser"
        os.environ["DATABASE_PASSWORD"] = "not_a_real_password"
        os.environ["DATABASE_POOL_SIZE"] = "20"
        os.environ["DATABASE_MAX_OVERFLOW"] = "30"
        os.environ["DATABASE_POOL_TIMEOUT"] = "90"
        os.environ["DATABASE_POOL_RECYCLE"] = "14400"
        os.environ["DATABASE_POOL_PRE_PING"] = "false"

        # Empty YAML
        yaml_content = yaml.dump({})

        with patch("importlib.resources.open_text", mock_open(read_data=yaml_content)):
            settings = Settings.from_yaml_env()

            # Verify all values from environment
            assert settings.app.name == "Env App"
            assert settings.app.host == "0.0.0.0"
            assert settings.app.port == 3000
            assert settings.app.version == "3.0.0"
            assert settings.app.environment == "prod"
            assert settings.app.workers == 10
            assert settings.app.debug is False

            assert settings.logging.level == "CRITICAL"
            assert settings.logging.json_format is True
            assert settings.logging.file_enabled is True
            assert settings.logging.file_path == "logs/env.log"
            assert settings.logging.rotation == "20 MB"
            assert settings.logging.retention == "30 days"
            assert settings.logging.backtrace is False
            assert settings.logging.diagnose is False
            assert settings.logging.colorize is True
            assert settings.logging.enqueue is True
            assert settings.logging.service_name == "env-service"

            assert settings.database.driver == "mysql"
            assert settings.database.host == "db.example.com"
            assert settings.database.port == 3306
            assert settings.database.name == "envdb"
            assert settings.database.user == "envuser"
            assert settings.database.password == "not_a_real_password"
            assert settings.database.pool_size == 20
            assert settings.database.max_overflow == 30
            assert settings.database.pool_timeout == 90
            assert settings.database.pool_recycle == 14400
            assert settings.database.pool_pre_ping is False

