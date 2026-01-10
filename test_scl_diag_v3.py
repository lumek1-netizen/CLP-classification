
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
    print("--- 🧪 KOMPLEXNÍ DIAGNOSTIKA SCL v3 ---")
    
    # 1. Testovací látky
    test_sub1 = "TEST_ADITIV_SCL"
    test_sub2 = "TEST_ENV_SCL"
    
    for name in [test_sub1, test_sub2]:
        existing = Substance.query.filter_by(name=name).first()
        if existing:
            db.session.delete(existing)
    db.session.commit()

    # Látka 1: Skin Corr. 1A se SCL >= 1% (GCL je 5%)
    sub1 = Substance(
        name=test_sub1,
        health_h_phrases="H314",
        scl_limits="Skin Corr. 1A: >= 1.0"
    )
    # Látka 2: Aquatic Acute 1 se SCL >= 5% (GCL je 25%)
    sub2 = Substance(
        name=test_sub2,
        env_h_phrases="H400",
        scl_limits="Aquatic Acute 1: >= 5.0"
    )
    db.session.add_all([sub1, sub2])
    db.session.commit()

    # 2. Test exportu
    csv_data = export_substances_to_csv()
    if "Skin Corr. 1A: >= 1.0" in csv_data and "Aquatic Acute 1: >= 5.0" in csv_data:
        print("✅ Všechna SCL nalezena v CSV exportu.")
    else:
        print("❌ SCL v exportu CHYBÍ!")

    # 3. Test klasifikace - Skin (Aditivní)
    mix_skin = Mixture(name="MIX_SKIN")
    db.session.add(mix_skin)
    db.session.flush()
    # 2% látky 1 by mělo triggerovat H314 přes SCL (1%), přestože je to < 5% GCL
    comp_skin = MixtureComponent(mixture_id=mix_skin.id, substance_id=sub1.id, concentration=2.0)
    db.session.add(comp_skin)
    run_clp_classification(mix_skin)
    
    if "H314" in mix_skin.final_health_hazards:
        print("✅ Skin SCL se správně projevilo (H314 při 2%, SCL 1%).")
    else:
        print("❌ Skin SCL SELHALO (H314 chybí)!")
        print(f"Log: {mix_skin.classification_log}")

    # 4. Test klasifikace - Aquatic (Environmentální)
    mix_env = Mixture(name="MIX_ENV")
    db.session.add(mix_env)
    db.session.flush()
    # 10% látky 2 by mělo triggerovat H400 přes SCL (5%), přestože je to < 25% GCL
    comp_env = MixtureComponent(mixture_id=mix_env.id, substance_id=sub2.id, concentration=10.0)
    db.session.add(comp_env)
    run_clp_classification(mix_env)
    
    if "H400" in mix_env.final_environmental_hazards:
        print("✅ Env SCL se správně projevilo (H400 při 10%, SCL 5%).")
    else:
        print("❌ Env SCL SELHALO (H400 chybí)!")
        print(f"Log: {mix_env.classification_log}")

    # Úklid
    db.session.delete(comp_skin)
    db.session.delete(comp_env)
    db.session.delete(mix_skin)
    db.session.delete(mix_env)
    db.session.delete(sub1)
    db.session.delete(sub2)
    db.session.commit()
    print("--- KONEC DIAGNOSTIKY ---")
