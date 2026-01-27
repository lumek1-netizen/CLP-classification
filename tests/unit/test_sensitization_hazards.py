"""
Testy pro klasifikaci Senzibilizace dýchacích cest a kůže.
"""
import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
from app.extensions import db

def test_skin_sens_1_classification(app):
    """Test klasifikace Skin Sens. 1 (H317) >= 1.0%."""
    with app.app_context():
        s = Substance(name="Skin Sens 1 Sub", health_h_phrases="H317")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Skin Sens 1 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 1.0% (Limit pro Skin Sens 1 obecně je 1.0%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=1.0))
        db.session.commit()

        run_clp_classification(mix)
        
        result = Mixture.query.get(mix.id)
        assert "H317" in result.final_health_hazards
        assert "GHS07" in result.final_ghs_codes

def test_resp_sens_1_classification(app):
    """Test klasifikace Resp. Sens. 1 (H334) >= 1.0%."""
    with app.app_context():
        s = Substance(name="Resp Sens 1 Sub", health_h_phrases="H334")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Resp Sens 1 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 1.0%
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=1.0))
        db.session.commit()

        run_clp_classification(mix)
        
        result = Mixture.query.get(mix.id)
        assert "H334" in result.final_health_hazards
        assert "GHS08" in result.final_ghs_codes

def test_sens_below_limit(app):
    """Test, že senzibilizace pod limitem (0.5% < 1.0%) neklasifikuje."""
    with app.app_context():
        s = Substance(name="Low Sens Sub", health_h_phrases="H317")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Low Sens Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 0.5% (pod limitem 1.0%, ale nad cutoff 0.1% - cutoff neklasifikuje, jen bere v potaz)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=0.5))
        db.session.commit()

        run_clp_classification(mix)
        
        result = Mixture.query.get(mix.id)
        assert "H317" not in result.final_health_hazards

def test_sens_non_additive(app):
    """Test, že senzibilizace není aditivní (dvě látky po 0.6% nedají dohromady limit 1.0%)."""
    with app.app_context():
        s1 = Substance(name="Sens Sub A", health_h_phrases="H317")
        s2 = Substance(name="Sens Sub B", health_h_phrases="H317")
        db.session.add_all([s1, s2])
        db.session.commit()

        mix = Mixture(name="Non-Additive Sens Mix")
        db.session.add(mix)
        db.session.commit()

        # Každá má 0.6%, dohromady 1.2%. Ale protože to není aditivní, ani jedna nepřekročí 1.0%.
        # Výsledek by měl být NEKLASIFIKOVÁNO.
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s1.id, concentration=0.6))
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s2.id, concentration=0.6))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H317" not in result.final_health_hazards

def test_sens_scl(app):
    """Test SCL pro senzibilizaci (látka s limitem nižším než 1.0%)."""
    with app.app_context():
        # Skin Sens. 1A má často limit 0.1%
        s = Substance(
            name="SCL Sens Sub", 
            health_h_phrases="H317",
            scl_limits="Skin Sens. 1: >= 0.2"
        )
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="SCL Sens Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 0.3% (Pod obecným 1.0%, ale nad SCL 0.2%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=0.3))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H317" in result.final_health_hazards
