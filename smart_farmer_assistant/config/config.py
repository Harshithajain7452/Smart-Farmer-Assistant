"""
Application configuration.

All settings are environment-driven so the same codebase runs locally,
on Render/Railway, or on AWS without code changes.
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _database_uri() -> str:
    """
    Build the SQLAlchemy URI.

    Priority:
      1. DATABASE_URL (Render / Railway / AWS RDS inject this)
      2. Individual MYSQL_* variables
      3. SQLite fallback so the project runs out-of-the-box for development
    """
    url = os.getenv("DATABASE_URL")
    if url:
        # Normalise legacy scheme used by some PaaS providers
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        return url

    if os.getenv("MYSQL_HOST"):
        user = os.getenv("MYSQL_USER", "root")
        password = os.getenv("MYSQL_PASSWORD", "")
        host = os.getenv("MYSQL_HOST", "localhost")
        port = os.getenv("MYSQL_PORT", "3306")
        name = os.getenv("MYSQL_DB", "smart_farmer")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"

    return "sqlite:///" + os.path.join(BASE_DIR, "smart_farmer.db")


class BaseConfig:
    """Shared configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production")

    # --- Database ---------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # --- Session / security ----------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    WTF_CSRF_TIME_LIMIT = None

    # --- Uploads ----------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB hard limit
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # --- Machine learning -------------------------------------------------
    MODEL_DIR = os.path.join(BASE_DIR, "trained_models")
    DATASET_DIR = os.path.join(BASE_DIR, "datasets")

    # --- Third-party APIs -------------------------------------------------
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    OPENWEATHER_GEO_URL = "https://api.openweathermap.org/geo/1.0"
    DATA_GOV_IN_API_KEY = os.getenv("DATA_GOV_IN_API_KEY", "")  # mandi prices
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")            # future chatbot LLM
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")  # optional, Leaflet default

    # --- i18n -------------------------------------------------------------
    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "हिन्दी",
        "kn": "ಕನ್ನಡ",
        "te": "తెలుగు",
        "ta": "தமிழ்",
        "mr": "मराठी",
        "gu": "ગુજરાતી",
        "pa": "ਪੰਜਾਬੀ",
        "bn": "বাংলা",
    }

    # --- Misc -------------------------------------------------------------
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@smartfarmer.in")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@1234")
    ITEMS_PER_PAGE = 15


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Return the config class selected by FLASK_ENV / APP_ENV."""
    env = os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development"
    return CONFIG_MAP.get(env, DevelopmentConfig)
