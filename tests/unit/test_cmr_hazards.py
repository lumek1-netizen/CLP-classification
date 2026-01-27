"""
Testy pro klasifikaci CMR (Karcinogenita, Mutagenita, Toxicita pro reprodukci).
"""
import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
from app.extensions import db

def test_carc_1a_classification(app):
    """Test klasifikace Carc. 1A (H350) >= 0.1%."""
    with app.app_context():
        s = Substance(name="Carc 1A Sub", health_h_phrases="H350")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Carc 1A Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 0.1% (Limit pro Carc 1A je obvykle 0.1%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=0.1))
        db.session.commit()

        run_clp_classification(mix)
        
        result = Mixture.query.get(mix.id)
        assert "H350" in result.final_health_hazards
        assert "GHS08" in result.final_ghs_codes

def test_carc_2_classification(app):
    """Test klasifikace Carc. 2 (H351) >= 1.0%."""
    with app.app_context():
        s = Substance(name="Carc 2 Sub", health_h_phrases="H351")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Carc 2 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 1.0% (Limit pro Carc 2 je 1.0%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=1.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H351" in result.final_health_hazards
        assert "GHS08" in result.final_ghs_codes

def test_muta_1b_classification(app):
    """Test klasifikace Muta. 1B (H340) >= 0.1%."""
    with app.app_context():
        s = Substance(name="Muta 1B Sub", health_h_phrases="H340")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Muta 1B Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 0.1%
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=0.1))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H340" in result.final_health_hazards

def test_repr_1b_classification(app):
    """Test klasifikace Repr. 1B (H360) >= 0.3%."""
    with app.app_context():
        s = Substance(name="Repr 1B Sub", health_h_phrases="H360D")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Repr 1B Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 0.3% (Limit pro Repr 1A/1B je 0.3%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=0.3))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H360D" in result.final_health_hazards

def test_repr_2_classification(app):
    """Test klasifikace Repr. 2 (H361) >= 3.0%."""
    with app.app_context():
        s = Substance(name="Repr 2 Sub", health_h_phrases="H361d")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Repr 2 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 3.0% (Limit pro Repr 2 je 3.0%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=3.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H361d" in result.final_health_hazards

def test_repro_below_limit(app):
    """Test, že pod limitem se neklasifikuje (Repr 1B < 0.3%)."""
    with app.app_context():
        s = Substance(name="Repr Sub Low", health_h_phrases="H360F")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="Repr Low Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 0.2% (< 0.3%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=0.2))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H360F" not in result.final_health_hazards

def test_cmr_scl_handling(app):
    """Test SCL pro Karcinogenitu (např. Formaldehyd má SCL)."""
    with app.app_context():
        # SCL syntaxe v systému: "Carc. 1B: >= 0.05" (příklad)
        # H350 je Carc 1B
        s = Substance(
            name="SCL Carc Sub", 
            health_h_phrases="H350",
            scl_limits="Carc. 1B: >= 0.05"
        )
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="SCL Carc Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 0.06% (Pod obecným limitem 0.1%, ale nad SCL 0.05%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=0.06))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H350" in result.final_health_hazards
