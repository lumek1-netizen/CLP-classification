"""
Testy pro klasifikaci STOT (Specific Target Organ Toxicity) - SE (Single Exposure) a RE (Repeated Exposure).
"""
import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
from app.extensions import db

def test_stot_se_1_classification(app):
    """Test klasifikace STOT SE 1 (H370) >= 10.0%."""
    with app.app_context():
        s = Substance(name="STOT SE 1 Sub", health_h_phrases="H370")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="STOT SE 1 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 10.0% (Limit pro STOT SE 1 je 10.0%)
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=10.0))
        db.session.commit()

        run_clp_classification(mix)
        
        result = Mixture.query.get(mix.id)
        assert "H370" in result.final_health_hazards
        assert "GHS08" in result.final_ghs_codes

def test_stot_se_2_classification(app):
    """Test klasifikace STOT SE 2 (H371) >= 10.0%."""
    with app.app_context():
        # STOT SE 2 se aktivuje mezi 1.0 a 10.0% u látky kat 1, nebo >= 10% u látky kat 2.
        # Zde testujeme látku, která má H371 (Kat 2)
        s = Substance(name="STOT SE 2 Sub", health_h_phrases="H371")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="STOT SE 2 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 10.0%
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=10.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H371" in result.final_health_hazards
        assert "GHS08" in result.final_ghs_codes

def test_stot_se_3_narcotic_summation(app):
    """Test aditivity pro STOT SE 3 (H336) - Narkotické účinky. Limit 20%."""
    with app.app_context():
        s1 = Substance(name="Narcotic A", health_h_phrases="H336")
        s2 = Substance(name="Narcotic B", health_h_phrases="H336")
        db.session.add_all([s1, s2])
        db.session.commit()

        mix = Mixture(name="Narcotic Sum Mix")
        db.session.add(mix)
        db.session.commit()

        # 15% + 6% = 21% >= 20% limit
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s1.id, concentration=15.0))
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s2.id, concentration=6.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H336" in result.final_health_hazards
        assert "GHS07" in result.final_ghs_codes

def test_stot_se_3_irritant_summation(app):
    """Test aditivity pro STOT SE 3 (H335) - Respirační dráždivost. Limit 20%."""
    with app.app_context():
        s1 = Substance(name="Irritant A", health_h_phrases="H335")
        s2 = Substance(name="Irritant B", health_h_phrases="H335")
        db.session.add_all([s1, s2])
        db.session.commit()

        mix = Mixture(name="Irritant Sum Mix")
        db.session.add(mix)
        db.session.commit()

        # 15% + 6% = 21% >= 20% limit
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s1.id, concentration=15.0))
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s2.id, concentration=6.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H335" in result.final_health_hazards

def test_stot_se_3_no_cross_summation(app):
    """Test, že se H335 a H336 nesčítají dohromady (různé cílové orgány)."""
    with app.app_context():
        s1 = Substance(name="Narcotic A", health_h_phrases="H336")
        s2 = Substance(name="Irritant B", health_h_phrases="H335")
        db.session.add_all([s1, s2])
        db.session.commit()

        mix = Mixture(name="No Cross Sum Mix")
        db.session.add(mix)
        db.session.commit()

        # 15% + 15% = 30%, ale každá zvlášť je < 20%
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s1.id, concentration=15.0))
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s2.id, concentration=15.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        # Nemělo by být ani jedno
        assert "H336" not in result.final_health_hazards
        assert "H335" not in result.final_health_hazards

def test_stot_re_1_classification(app):
    """Test klasifikace STOT RE 1 (H372) >= 10.0%."""
    with app.app_context():
        s = Substance(name="STOT RE 1 Sub", health_h_phrases="H372")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="STOT RE 1 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 10.0%
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=10.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H372" in result.final_health_hazards
        assert "GHS08" in result.final_ghs_codes

def test_stot_re_2_classification(app):
    """Test klasifikace STOT RE 2 (H373) >= 10.0%."""
    with app.app_context():
        s = Substance(name="STOT RE 2 Sub", health_h_phrases="H373")
        db.session.add(s)
        db.session.commit()

        mix = Mixture(name="STOT RE 2 Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 10.0%
        db.session.add(MixtureComponent(mixture_id=mix.id, substance_id=s.id, concentration=10.0))
        db.session.commit()

        run_clp_classification(mix)

        result = Mixture.query.get(mix.id)
        assert "H373" in result.final_health_hazards
