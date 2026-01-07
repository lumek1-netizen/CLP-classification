import os
import sys

# Přidání kořenového adresáře
sys.path.append(os.getcwd())

print("--- Start závěrečné verifikace ---")

try:
    from app import create_app
    from app.extensions import db
    from app.models import Substance, Mixture, MixtureComponent
    from app.services.clp import run_clp_classification
    
    app = create_app()
    print("✅ Application Factory (create_app) - OK")
    
    with app.app_context():
        print(f"✅ Modely SQLAlchemy - OK (Substance, Mixture, Component)")
        print(f"✅ Importy CLP Service - OK")
        
    print("--- Verifikace úspěšná ---")
except Exception as e:
    print(f"❌ Verifikace selhala: {e}")
    sys.exit(1)
