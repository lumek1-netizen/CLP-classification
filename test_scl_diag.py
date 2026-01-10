
import os
import sys

# Přidání cesty k projektu do sys.path
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp.engine import run_clp_classification
from app.services.export_service import export_substances_to_csv

app = create_app()

with app.app_context():
    print("--- 🧪 DIAGNOSTIKA SCL ---")
    
    # 1. Čištění a příprava testovací látky
    test_sub_name = "TEST_SCL_SUBSTANCE"
    existing = Substance.query.filter_by(name=test_sub_name).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        print(f"Smazána existující testovací látka.")

    # Vytvoření látky s SCL pro Acute Tox. 4 (H302)
    # Formát, který generuje JS a očekává parser
    scl_val = "Acute Tox. 4: >= 5.0"
    sub = Substance(
        name=test_sub_name,
        health_h_phrases="",  # Žádné standardní H-věty
        scl_limits=scl_val
    )
    db.session.add(sub)
    db.session.commit()
    print(f"Vytvořena látka '{test_sub_name}' s SCL: '{sub.scl_limits}'")

    # 2. Kontrola exportu
    csv_data = export_substances_to_csv()
    if scl_val in csv_data:
        print("✅ SCL nalezeno v CSV exportu.")
    else:
        print("❌ SCL CHYBÍ v CSV exportu!")
        # Debug výpis kousku CSV
        print("Ukázka CSV (posledních 200 znaků):")
        print(csv_data[-200:])

    # 3. Kontrola klasifikace
    mix = Mixture(name="TEST_SCL_MIXTURE")
    db.session.add(mix)
    db.session.flush()
    
    # Přidáme 6% látky (mělo by triggerovat SCL >= 5%)
    comp = MixtureComponent(mixture_id=mix.id, substance_id=sub.id, concentration=6.0)
    db.session.add(comp)
    
    run_clp_classification(mix)
    
    print(f"--- Výsledek klasifikace (6% látky se SCL >= 5%): ---")
    print(f"H-věty: {mix.final_health_hazards}")
    print(f"GHS: {mix.final_ghs_codes}")
    
    if "H302" in mix.final_health_hazards:
        print("✅ SCL se projevilo v klasifikaci (H302 nalezeno).")
    else:
        print("❌ SCL se PROJEVILO v klasifikaci (H302 chybí)!")
        print("Log klasifikace:")
        for log in mix.classification_log:
            print(f"  - {log.get('step')}: {log.get('result')} | {log.get('detail')}")

    # Úklid
    db.session.delete(comp)
    db.session.delete(mix)
    db.session.delete(sub)
    db.session.commit()
    print("--- KONEC DIAGNOSTIKY ---")
