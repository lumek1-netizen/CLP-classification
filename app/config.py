import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Validace SECRET_KEY v produkci
    if not SECRET_KEY:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError("SECRET_KEY musí být nastaven v produkčním prostředí!")
        else:
            # Pouze pro development - vygenerovat dočasný klíč
            import secrets

            SECRET_KEY = secrets.token_hex(32)
            print(
                "VAROVÁNÍ: Používá se dočasný SECRET_KEY. Nastavte SECRET_KEY v .env souboru!"
            )

    db_url = os.environ.get("DATABASE_URL")

    if db_url and db_url.startswith("sqlite:///"):
        # Check if it's already an absolute path (sqlite://// on Linux or sqlite:///C: on Windows)
        path = db_url.replace("sqlite:///", "")
        if not os.path.isabs(path):
            db_url = "sqlite:///" + os.path.join(basedir, path)

    SQLALCHEMY_DATABASE_URI = db_url or "sqlite:///" + os.path.join(
        basedir, "instance", "clp_calculator.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Caching
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 3600))

    # Security limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit for uploads
