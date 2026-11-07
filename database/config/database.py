"""
Centralized PostgreSQL Database Configuration for InChi Pilot Gateway.

This module provides a reusable, environment-driven database configuration
function `get_database_config()` designed to be imported by the Django application
and reused across all backend developers' local and deployment environments.

Key Design & Engineering Principles:
1. Environment-driven: Reads all database credentials from environment variables.
   No credentials, passwords, or secrets are hardcoded in source code.
2. Strict Validation: Upfront validation of all required connection parameters,
   failing fast with actionable error messages if improperly configured.
3. Connection Reuse (CONN_MAX_AGE): Reuses open database connections across HTTP
   requests on each worker thread (default: 60s), eliminating costly TCP/TLS
   connection setup overhead.
4. Connection Health Checks (CONN_HEALTH_CHECKS): Enabled by default (Django 4.1+)
   to verify connection liveness before reuse, preventing stale connection errors
   after network drops or container restarts.
5. Connection Pooling Evaluation: Django 5.1+ natively supports psycopg_pool
   via `OPTIONS: {"pool": True}` or a configuration dict. This can be optionally
   toggled via `DB_POOL_ENABLED=True`.
6. Architectural Separation: Free of any application business logic, models, or views.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def validate_database_env(
    name: str | None,
    user: str | None,
    password: str | None,
    host: str | None,
    port: str | int | None,
    conn_max_age: str | int | None,
) -> tuple[str, str, str, str, int, int]:
    """
    Validate that all required database configuration parameters are present and well-formed.

    Args:
        name: PostgreSQL database name (DB_NAME).
        user: PostgreSQL database username (DB_USER).
        password: PostgreSQL database password (DB_PASSWORD).
        host: PostgreSQL database host (DB_HOST).
        port: PostgreSQL port (DB_PORT).
        conn_max_age: Database connection max age in seconds (DB_CONN_MAX_AGE).

    Returns:
        tuple: (name, user, password, host, port, conn_max_age) in their parsed types.

    Raises:
        ImproperlyConfigured: If any required parameter is missing or malformed.
    """
    missing: list[str] = []

    if not name or not str(name).strip():
        missing.append("DB_NAME")
    if not user or not str(user).strip():
        missing.append("DB_USER")
    if password is None:
        missing.append("DB_PASSWORD")
    if not host or not str(host).strip():
        missing.append("DB_HOST")
    if port is None or str(port).strip() == "":
        missing.append("DB_PORT")

    if missing:
        raise ImproperlyConfigured(
            f"Missing required database environment variable(s): {', '.join(missing)}. "
            "Please configure them in your .env file or environment. "
            "Refer to .env.example for required values."
        )

    # Validate port range
    try:
        parsed_port = int(str(port).strip())
        if not (1 <= parsed_port <= 65535):
            raise ValueError(f"Port out of range: {parsed_port}")
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"Invalid DB_PORT '{port}'. DB_PORT must be an integer between 1 and 65535."
        ) from exc

    # Validate conn_max_age (must be non-negative)
    try:
        parsed_conn_max_age = int(str(conn_max_age).strip()) if conn_max_age is not None else 60
        if parsed_conn_max_age < 0:
            raise ValueError(f"CONN_MAX_AGE cannot be negative: {parsed_conn_max_age}")
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"Invalid DB_CONN_MAX_AGE '{conn_max_age}'. DB_CONN_MAX_AGE must be a non-negative integer."
        ) from exc

    return (
        str(name).strip(),
        str(user).strip(),
        str(password),
        str(host).strip(),
        parsed_port,
        parsed_conn_max_age,
    )


def get_database_config(base_dir: Path | None = None) -> Dict[str, Any]:
    """
    Construct and return a Django-compatible DATABASES dictionary.

    Resolution order:
    1. If `USE_SQLITE=True` is explicitly set in environment, returns a local SQLite
       configuration (useful for offline unit testing without Docker).
    2. If `DATABASE_URL` is set, parses connection parameters from the URL.
    3. Standard PostgreSQL: reads discrete environment variables:
       - DB_NAME (default: "inchi_db")
       - DB_USER (default: "inchi_user")
       - DB_PASSWORD (default: "change_me")
       - DB_HOST (default: "localhost")
       - DB_PORT (default: "5432")
       - DB_CONN_MAX_AGE (default: "60")
       - DB_CONN_HEALTH_CHECKS (default: "True")
       - DB_POOL_ENABLED (default: "False")
       - DB_POOL_MIN_CONNS (default: "1")
       - DB_POOL_MAX_CONNS (default: "10")
       - DB_POOL_TIMEOUT (default: "30.0")

    Returns:
        dict: Django DATABASES configuration dictionary.
    """
    # 1. Optional explicit SQLite fallback (for isolated offline tests)
    use_sqlite = os.getenv("USE_SQLITE", "False").lower() in ("true", "1", "yes")
    if use_sqlite:
        sqlite_path = (base_dir or Path.cwd()) / "db.sqlite3"
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": sqlite_path,
            }
        }

    # 2. Check for optional DATABASE_URL override
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        parsed_url = urlparse(database_url)
        if parsed_url.scheme in ("postgres", "postgresql", "pgsql"):
            db_name = parsed_url.path.lstrip("/")
            db_user = parsed_url.username or ""
            db_password = parsed_url.password or ""
            db_host = parsed_url.hostname or "localhost"
            db_port = parsed_url.port or 5432
            db_conn_max_age = os.getenv("DB_CONN_MAX_AGE", "60")
        elif parsed_url.scheme == "sqlite":
            sqlite_path = parsed_url.path or str((base_dir or Path.cwd()) / "db.sqlite3")
            return {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": sqlite_path,
                }
            }
        else:
            raise ImproperlyConfigured(
                f"Unsupported database scheme '{parsed_url.scheme}' in DATABASE_URL."
            )
    else:
        # 3. Discrete environment variables
        db_name = os.getenv("DB_NAME", "inchi_db")
        db_user = os.getenv("DB_USER", "inchi_user")
        db_password = os.getenv("DB_PASSWORD", "change_me")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_conn_max_age = os.getenv("DB_CONN_MAX_AGE", "60")

    # Validate parameters
    valid_name, valid_user, valid_password, valid_host, valid_port, valid_conn_max_age = (
        validate_database_env(
            name=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            conn_max_age=db_conn_max_age,
        )
    )

    # Connection health check configuration (supported in Django 4.1+)
    conn_health_checks = os.getenv("DB_CONN_HEALTH_CHECKS", "True").lower() in ("true", "1", "yes")

    # Database OPTIONS dictionary
    options: Dict[str, Any] = {}

    # Optional Connection Pooling (Django 5.1+ / psycopg_pool)
    pool_enabled = os.getenv("DB_POOL_ENABLED", "False").lower() in ("true", "1", "yes")
    if pool_enabled:
        try:
            import psycopg_pool  # noqa: F401
            pool_min = int(os.getenv("DB_POOL_MIN_CONNS", "1"))
            pool_max = int(os.getenv("DB_POOL_MAX_CONNS", "10"))
            pool_timeout = float(os.getenv("DB_POOL_TIMEOUT", "30.0"))
            options["pool"] = {
                "min_size": pool_min,
                "max_size": pool_max,
                "timeout": pool_timeout,
            }
            logger.info(
                "psycopg_pool connection pooling enabled: min=%d, max=%d, timeout=%.1fs",
                pool_min,
                pool_max,
                pool_timeout,
            )
        except ImportError:
            logger.warning(
                "DB_POOL_ENABLED is True, but 'psycopg_pool' is not installed. "
                "Falling back to standard persistent connections (CONN_MAX_AGE)."
            )

    database_config: Dict[str, Any] = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": valid_name,
            "USER": valid_user,
            "PASSWORD": valid_password,
            "HOST": valid_host,
            "PORT": valid_port,
            "CONN_MAX_AGE": valid_conn_max_age,
            "CONN_HEALTH_CHECKS": conn_health_checks,
        }
    }

    if options:
        database_config["default"]["OPTIONS"] = options

    return database_config

