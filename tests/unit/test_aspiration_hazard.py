"""
Testy pro klasifikaci Aspirační toxicity (H304).
"""
import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
from app.extensions import db

def test_aspiration_category_1_single_component(app):
    """Test klasifikace Asp. Tox. 1 (H304) >= 10.0% (jedna složka)."""
    with app.app_context():
        s = Substance(name="Asp Tox Sub", health_h_phrases="H304")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Asp Tox Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 10.0%
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=10.0))
        db.session.commit()

        run_clp_classification(mix)
        
        result = Mixture.query.get(mix.id)
        assert "H304" in result.final_health_hazards
        assert "GHS08" in result.final_ghs_codes

def test_aspiration_summation(app):
    """Test aditivity pro Asp. Tox. 1. Suma koncentrací >= 10%."""
    with app.app_context():
        s1 = Substance(name="Asp Sub A", health_h_phrases="H304")
        s2 = Substance(name="Asp Sub B", health_h_phrases="H304")
        db.session.add_all([s1, s2])
        db.session.commit()

        mix = Mixture(name="Asp Sum Mix")
        db.session.add(mix)
        db.session.commit()

        # 6% + 6% = 12% >= 10% limit
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s1.id, concentration=6.0))
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s2.id, concentration=6.0))
        db.session.commit()

        run_clp_classification(mix)
        
        result = Mixture.query.get(mix.id)
        # Očekáváme H304, protože se H304 látky sčítají (CLP 3.10.3.3.1)
        assert "H304" in result.final_health_hazards
