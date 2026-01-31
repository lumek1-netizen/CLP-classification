import sqlite3
import os
import sys

# Přidání cesty k modulu app
sys.path.append(os.getcwd())

from app import create_app
from app.models import Mixture, MixtureComponent, Substance
from app.services.clp.health import HealthHazardClassifier

def verify_fix(mixture_id):
    app = create_app()
    with app.app_context():
        mixture = Mixture.query.get(mixture_id)
        if not mixture:
            print(f"Směs {mixture_id} nenalezena.")
            return

        classifier = HealthHazardClassifier(mixture)
        hazards, ghs, logs = classifier.classify()
        
        print(f"OVĚŘENÍ SMĚSI: {mixture.name}")
        print(f"Výsledné H-věty: {hazards}")
        
        if "H317" in hazards:
            print("SUCCESS: H317 je nyní správně přítomno!")
            
            # Najít log pro H317
            h317_logs = [l for l in logs if l.get('result') == 'H317' or 'Skin Sens' in l.get('step', '')]
            for log in h317_logs:
                print(f"LOG: {log['step']} -> {log['detail']} -> {log['result']}")
        else:
            print("FAIL: H317 stále chybí!")

if __name__ == "__main__":
    verify_fix(5)
