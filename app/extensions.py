from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
cache = Cache()

# === Rate Limiter ===
limiter = Limiter(
    key_func=get_remote_address,  # Limituj podle IP adresy
    default_limits=["200 per day", "50 per hour"],  # Globální limity
    storage_uri="memory://",  # Pro produkci použij Redis
)
