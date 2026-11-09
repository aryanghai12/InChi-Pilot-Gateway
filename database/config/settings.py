"""
Django settings for InChi Pilot Gateway.

This configuration integrates the centralized database connection defined in
`config/database.py` and loads credentials securely from `.env`.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file at project root
load_dotenv(BASE_DIR / ".env")

# Core Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-in-production-inchi-gateway-2026")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
]

# Centralized PostgreSQL Database Configuration
from config.database import get_database_config  # noqa: E402

DATABASES = get_database_config(base_dir=BASE_DIR)

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

