import os
import sys
from pathlib import Path

# Make `src.*` imports available for all tests.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Provide deterministic defaults in CI when env/local.env is not mounted.
_REQUIRED_ENV_DEFAULTS = {
    "DATABASE_DRIVER": "postgresql",
    "DATABASE_HOST": "localhost",
    "DATABASE_PORT": "5432",
    "DATABASE_NAME": "test_db",
    "DATABASE_USER": "test_user",
    "DATABASE_PASSWORD": "test_password",
    "DATABASE_POOL_SIZE": "5",
    "DATABASE_MAX_OVERFLOW": "10",
    "DATABASE_POOL_TIMEOUT": "30",
    "DATABASE_POOL_RECYCLE": "3600",
    "DATABASE_POOL_PRE_PING": "true",
    "TOKEN_SECRET_KEY": "test-secret-key",
    "TOKEN_ALGORITHM": "HS256",
    "TOKEN_HTTP_ONLY": "true",
    "TOKEN_SECURE": "false",
    "TOKEN_SAME_SITE": "lax",
    "TOKEN_EXPIRATION": "15",
}

for key, value in _REQUIRED_ENV_DEFAULTS.items():
    os.environ.setdefault(key, value)

