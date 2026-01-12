
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
    print("--- 🧪 KOMPLEXNÍ DIAGNOSTIKA SCL v4 (Enhanced Parser) ---")
    
    # 1. Testovací látky se starým formátem (zpětná kompatibilita)
    test_sub1 = "TEST_ADITIV_SCL_OLD"
    test_sub2 = "TEST_ENV_SCL_OLD"
    
    # 2. Testovací látky s novým formátem (uživatelsky přívětivý)
    test_sub3 = "TEST_NEWFORMAT_SCL"
    
    for name in [test_sub1, test_sub2, test_sub3]:
        existing = Substance.query.filter_by(name=name).first()
        if existing:
            db.session.delete(existing)
    db.session.commit()

    # Látka 1: Starý formát - Skin Corr. 1A se SCL >= 1% (GCL je 5%)
    sub1 = Substance(
        name=test_sub1,
        health_h_phrases="H314",
        scl_limits="Skin Corr. 1A: >= 1.0"
    )
    
    # Látka 2: Starý formát - Aquatic Acute 1 se SCL >= 5% (GCL je 25%)
    sub2 = Substance(
        name=test_sub2,
        env_h_phrases="H400",
        scl_limits="Aquatic Acute 1: >= 5.0"
    )
    
    # Látka 3: NOVÝ FORMÁT - s novými řádky, rozsahy, procenty, H-kódy, desetinnými čárkami
    # Simuluje vstup uživatele z reportované chyby
    sub3 = Substance(
        name=test_sub3,
        health_h_phrases="H319, H315, H318, H332, H330",
        scl_limits="""Eye Irrit. 2; H319
1 - 30 %
Skin Irrit. 2; H315
> 30 %
Eye Dam. 1; H318
> 30 - 100 %
Acute Tox. 4; H332
<= 34,5 %
Acute Tox. 2; H330
> 34,5 %"""
    )
    
    db.session.add_all([sub1, sub2, sub3])
    db.session.commit()

    # 2. Test exportu
    csv_data = export_substances_to_csv()
    if "Skin Corr. 1A" in csv_data and "Aquatic Acute 1" in csv_data:
        print("✅ Všechna SCL (starý formát) nalezena v CSV exportu.")
    else:
        print("❌ SCL (starý formát) v exportu CHYBÍ!")

    # 3. Test klasifikace - Skin (Aditivní) - STARÝ FORMÁT
    mix_skin = Mixture(name="MIX_SKIN_OLD")
    db.session.add(mix_skin)
    db.session.flush()
    # 2% látky 1 by mělo triggerovat H314 přes SCL (1%), přestože je to < 5% GCL
    comp_skin = MixtureComponent(mixture_id=mix_skin.id, substance_id=sub1.id, concentration=2.0)
    db.session.add(comp_skin)
    run_clp_classification(mix_skin)
    
    if "H314" in mix_skin.final_health_hazards:
        print("✅ Skin SCL (starý formát) se správně projevilo (H314 při 2%, SCL 1%).")
    else:
        print("❌ Skin SCL (starý formát) SELHALO (H314 chybí)!")
        print(f"Log: {mix_skin.classification_log}")

    # 4. Test klasifikace - NOVÝ FORMÁT
    # Skin Irrit. 2 má SCL "> 30%", takže při 35% by mělo triggerovat H315
    mix_newformat = Mixture(name="MIX_NEWFORMAT")
    db.session.add(mix_newformat)
    db.session.flush()
    comp_newformat = MixtureComponent(mixture_id=mix_newformat.id, substance_id=sub3.id, concentration=35.0)
    db.session.add(comp_newformat)
    run_clp_classification(mix_newformat)
    
    if "H315" in mix_newformat.final_health_hazards:
        print("✅ Nový formát SCL se správně projevilo (H315 při 35%, SCL > 30%).")
    else:
        print("❌ Nový formát SCL SELHALO (H315 chybí)!")
        print(f"Log: {mix_newformat.classification_log}")
    
    # 5. Test Eye Dam. 1 s novým formátem (rozsah "> 30 - 100 %" → "> 30")
    if "H318" in mix_newformat.final_health_hazards:
        print("✅ Eye Dam. 1 v novém formátu funguje (H318 při 35%, SCL > 30%).")
    else:
        print("❌ Eye Dam. 1 v novém formátu SELHALO!")

    # 6. Test Acute Tox. 2 s desetinnou čárkou "> 34,5 %" → "> 34.5"
    if "H330" in mix_newformat.final_health_hazards:
        print("✅ Acute Tox. 2 s desetinnou čárkou funguje (H330 při 35%, SCL > 34.5%).")
    else:
        print("❌ Acute Tox. 2 s desetinnou čárkou SELHALO!")
    
    # Úklid
    db.session.delete(comp_skin)
    db.session.delete(comp_newformat)
    db.session.delete(mix_skin)
    db.session.delete(mix_newformat)
    db.session.delete(sub1)
    db.session.delete(sub2)
    db.session.delete(sub3)
    db.session.commit()
    print("--- KONEC DIAGNOSTIKY ---")
