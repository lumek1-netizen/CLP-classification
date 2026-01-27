"""
Spouštěcí skript aplikace CLP Calculator.

Tento soubor slouží jako vstupní bod pro spuštění Flask aplikace.
Načítá konfiguraci z prostředí a spouští vývojový server.
"""

import os
from app import create_app

# Načtení konfigurace prostředí (výchozí je 'development')
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Debug režim povolen pouze v development prostředí
    debug_mode = config_name == 'development'
    app.run(debug=debug_mode)
