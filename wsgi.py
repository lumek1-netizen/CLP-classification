"""
WSGI entry point pro produkční nasazení.
"""
import os
from app import create_app

# Načti prostředí z environment variable
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == "__main__":
    app.run()
