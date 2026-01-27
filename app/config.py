import os
from dotenv import load_dotenv
import warnings
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, ".env"))


# === VALIDACE SECRET_KEY ===
_secret_key = os.environ.get("SECRET_KEY")

if not _secret_key:
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError(
            "SECRET_KEY musí být nastaven v produkčním prostředí! "
            "Vygeneruj pomocí: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    else:
        import secrets
        _secret_key = secrets.token_hex(32)
        warnings.warn(
            "⚠️  VAROVÁNÍ: Používá se dočasný SECRET_KEY. "
            "Nastavte SECRET_KEY v .env souboru!",
            UserWarning
        )

_weak_keys = ['dev-key', 'test-key', 'secret', 'changeme', '12345']
if _secret_key and any(weak in _secret_key.lower() for weak in _weak_keys):
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError("SECRET_KEY je příliš slabý pro produkci!")
    else:
        warnings.warn("⚠️  VAROVÁNÍ: SECRET_KEY vypadá slabě!", UserWarning)


class Config:
    """Základní konfigurace pro všechna prostředí."""
    SECRET_KEY = _secret_key
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Caching
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 3600))
    
    # Security limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Konfigurace pro development prostředí."""
    DEBUG = True
    TESTING = False
    
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        path = db_url.replace("sqlite:///", "")
        if not os.path.isabs(path):
            db_url = "sqlite:///" + os.path.join(basedir, path)
    
    SQLALCHEMY_DATABASE_URI = db_url or "sqlite:///" + os.path.join(
        basedir, "instance", "clp_calculator.db"
    )
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Konfigurace pro production prostředí."""
    DEBUG = False
    TESTING = False
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    if not SQLALCHEMY_DATABASE_URI and os.environ.get("FLASK_ENV") == "production":
        raise ValueError("DATABASE_URL musí být nastaven v produkčním prostředí!")
    
    # PostgreSQL connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }
    
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Redis cache/limiter (volitelné, pokud je REDIS_URL)
    _redis_url = os.environ.get('REDIS_URL')
    if _redis_url:
        CACHE_TYPE = "RedisCache"
        CACHE_REDIS_URL = _redis_url
        RATELIMIT_STORAGE_URL = _redis_url


class TestingConfig(Config):
    """Konfigurace pro testování."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Mapa konfigurací
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}

def get_config(config_name=None):
    """Vrátí konfigurační třídu podle jména prostředí."""
    if config_name is not None and not isinstance(config_name, str):
        return config_name
        
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_map.get(config_name, DevelopmentConfig)
