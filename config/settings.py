import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-in-production-inchi-gateway-2026")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

# Application definition
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",

    # InChi Core Apps
    "apps.accounts.apps.AccountsConfig",
    "apps.registry.apps.RegistryConfig",
    "apps.readiness.apps.ReadinessConfig",
    "apps.demand.apps.DemandConfig",
    "apps.matching.apps.MatchingConfig",
    "apps.opportunities.apps.OpportunitiesConfig",
    "apps.audit.apps.AuditConfig",
    "apps.dashboard.apps.DashboardConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.CorrelationIdMiddleware",  # InChi Request Correlation Tracking
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database Configuration
# Fallback to local SQLite if DATABASE_URL is not set
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    import urllib.parse
    parsed_db = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_db.path.lstrip("/"),
            "USER": parsed_db.username,
            "PASSWORD": parsed_db.password,
            "HOST": parsed_db.hostname,
            "PORT": parsed_db.port or 5432,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework (DRF)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",  # Deny-by-default
    ],
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular OpenAPI Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "InChi Pilot Gateway API",
    "DESCRIPTION": "Private internal API for BNCS InChi Pilot Gateway (Supplier & Demand Matching)",
    "VERSION": "v0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# Session & Cookie Security
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", 28800))  # 8 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")

CSRF_COOKIE_HTTPONLY = False  # Allows Next.js frontend to read token for X-CSRFToken header
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False").lower() in ("true", "1")

# CSRF Trusted Origins & CORS
csrf_trusted = os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted.split(",") if origin.strip()]

cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

# Admin Path
ADMIN_URL_PATH = os.getenv("ADMIN_URL_PATH", "admin/").strip("/") + "/"
