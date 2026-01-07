import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.extensions import db
from app.services.clp.engine import run_clp_classification

def test_acute_tox_scl_classification(app):
    with app.app_context():
        # 1. Vytvoření látky se SCL pro Acute Tox. 3 (H301) při C >= 5%
        # Normálně by 5% látky s ATE 500 (Cat 4) nevedlo k H301
        substance = Substance(
            name="SCL Test Substance",
            ate_oral=500,  # Kategorie 4
            health_h_phrases="H302",
            scl_limits="Acute Tox. 3: >= 5.0"
        )
        db.session.add(substance)
        db.session.commit()

        # 2. Vytvoření směsi s 6% této látky
        mixture = Mixture(name="SCL Test Mixture")
        db.session.add(mixture)
        db.session.flush()

        component = MixtureComponent(
            mixture_id=mixture.id,
            substance_id=substance.id,
            concentration=6.0
        )
        db.session.add(component)
        db.session.commit()

        # 3. Spuštění klasifikace
        run_clp_classification(mixture)
        
        # Výsledky jsou uloženy v objektu mixture
        print(f"DEBUG TEST: Final Hazards: {mixture.final_health_hazards}")
        
        # H301 by mělo být v hazardech díky SCL
        assert "H301" in mixture.final_health_hazards
        assert "GHS06" in mixture.final_ghs_codes
        
        print("Test SCL pro Acute Tox proběhl úspěšně.")
