"""
Inicializace Flask rozšíření.

Obsahuje definice a konfiguraci SQLAlchemy, Migrate, CSRF, LoginManager, Cache a Limiter.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
cache = Cache()
talisman = Talisman()

# === Rate Limiter ===
limiter = Limiter(
    key_func=get_remote_address,  # Limituj podle IP adresy
    default_limits=["200 per day", "50 per hour"],  # Globální limity
    storage_uri="memory://",  # Pro produkci použij Redis
)
