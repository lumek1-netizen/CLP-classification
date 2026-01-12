"""
Testy pro klasifikaci akutní toxicity (Acute Tox 3/4) podle koncentračních limitů.
Testuje dermální, orální a inhalační cesty expozice.
"""
import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
from app.extensions import db


def test_acute_tox_4_dermal_classification(app):
    """Test klasifikace Acute Tox 4 (Dermal) s H312."""
    with app.app_context():
        # Látka s H312 (Acute Tox 4 - Dermal)
        s1 = Substance(
            name="Dermal Toxic Substance",
            health_h_phrases="H312",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Dermal Tox Test Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 30 % (> 25 % GCL pro Acute Tox 4)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=30.0
        )
        db.session.add(comp)
        db.session.commit()

        # Spuštění klasifikace
        run_clp_classification(mix)
        db.session.commit()

        # Ověření
        retrieved_mix = Mixture.query.get(mix.id)
        assert "H312" in retrieved_mix.final_health_hazards, \
            f"H312 chybí v {retrieved_mix.final_health_hazards}"
        assert "GHS07" in retrieved_mix.final_ghs_codes, \
            f"GHS07 chybí v {retrieved_mix.final_ghs_codes}"


def test_acute_tox_3_dermal_classification(app):
    """Test klasifikace Acute Tox 3 (Dermal) s H311."""
    with app.app_context():
        s1 = Substance(
            name="Highly Dermal Toxic Substance",
            health_h_phrases="H311",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Dermal Tox 3 Test Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 15 % (> 10 % GCL pro Acute Tox 3)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=15.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        assert "H311" in retrieved_mix.final_health_hazards, \
            f"H311 chybí v {retrieved_mix.final_health_hazards}"
        assert "GHS06" in retrieved_mix.final_ghs_codes, \
            f"GHS06 chybí v {retrieved_mix.final_ghs_codes}"


def test_acute_tox_4_dermal_below_limit(app):
    """Test, že pod limitem není klasifikováno."""
    with app.app_context():
        s1 = Substance(
            name="Low Dermal Toxic Substance",
            health_h_phrases="H312",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Below Limit Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 20 % (< 25 % GCL)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=20.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        assert "H312" not in retrieved_mix.final_health_hazards, \
            f"H312 by nemělo být v {retrieved_mix.final_health_hazards}"


def test_acute_tox_4_dermal_with_scl(app):
    """Test SCL pro Acute Tox 4 (Dermal)."""
    with app.app_context():
        s1 = Substance(
            name="SCL Dermal Toxic Substance",
            health_h_phrases="H312",
            scl_limits="Acute Tox. 4 (Dermal): >= 5.0"  # Snížený limit
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="SCL Dermal Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 8 % (< 25 % GCL, ale > 5 % SCL)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=8.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        assert "H312" in retrieved_mix.final_health_hazards, \
            f"H312 chybí v {retrieved_mix.final_health_hazards} (SCL test)"
        assert "GHS07" in retrieved_mix.final_ghs_codes, \
            f"GHS07 chybí v {retrieved_mix.final_ghs_codes} (SCL test)"


def test_acute_tox_4_oral_classification(app):
    """Test klasifikace Acute Tox 4 (Oral) s H302."""
    with app.app_context():
        s1 = Substance(
            name="Oral Toxic Substance",
            health_h_phrases="H302",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Oral Tox Test Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 30 % (> 25 % GCL)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=30.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        assert "H302" in retrieved_mix.final_health_hazards, \
            f"H302 chybí v {retrieved_mix.final_health_hazards}"
        assert "GHS07" in retrieved_mix.final_ghs_codes, \
            f"GHS07 chybí v {retrieved_mix.final_ghs_codes}"


def test_acute_tox_3_oral_classification(app):
    """Test klasifikace Acute Tox 3 (Oral) s H301."""
    with app.app_context():
        s1 = Substance(
            name="Highly Oral Toxic Substance",
            health_h_phrases="H301",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Oral Tox 3 Test Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 12 % (> 10 % GCL)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=12.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        assert "H301" in retrieved_mix.final_health_hazards, \
            f"H301 chybí v {retrieved_mix.final_health_hazards}"
        assert "GHS06" in retrieved_mix.final_ghs_codes, \
            f"GHS06 chybí v {retrieved_mix.final_ghs_codes}"


def test_acute_tox_4_inhalation_classification(app):
    """Test klasifikace Acute Tox 4 (Inhalation) s H332."""
    with app.app_context():
        s1 = Substance(
            name="Inhalation Toxic Substance",
            health_h_phrases="H332",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Inhalation Tox Test Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 30 % (> 25 % GCL)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=30.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        assert "H332" in retrieved_mix.final_health_hazards, \
            f"H332 chybí v {retrieved_mix.final_health_hazards}"
        assert "GHS07" in retrieved_mix.final_ghs_codes, \
            f"GHS07 chybí v {retrieved_mix.final_ghs_codes}"


def test_acute_tox_3_inhalation_classification(app):
    """Test klasifikace Acute Tox 3 (Inhalation) s H331."""
    with app.app_context():
        s1 = Substance(
            name="Highly Inhalation Toxic Substance",
            health_h_phrases="H331",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Inhalation Tox 3 Test Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 15 % (> 10 % GCL)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=15.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        assert "H331" in retrieved_mix.final_health_hazards, \
            f"H331 chybí v {retrieved_mix.final_health_hazards}"
        assert "GHS06" in retrieved_mix.final_ghs_codes, \
            f"GHS06 chybí v {retrieved_mix.final_ghs_codes}"


def test_acute_tox_multiple_routes(app):
    """Test klasifikace s více cestami expozice současně."""
    with app.app_context():
        # Látka s více H-větami
        s1 = Substance(
            name="Multi-route Toxic Substance",
            health_h_phrases="H311, H302, H332",
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Multi-route Mix")
        db.session.add(mix)
        db.session.commit()

        # Koncentrace 30 % (> všechny limity)
        comp = MixtureComponent(
            mixture_id=mix.id,
            substance_id=s1.id,
            concentration=30.0
        )
        db.session.add(comp)
        db.session.commit()

        run_clp_classification(mix)
        db.session.commit()

        retrieved_mix = Mixture.query.get(mix.id)
        # Měly by být všechny tři H-věty
        assert "H311" in retrieved_mix.final_health_hazards, \
            f"H311 chybí v {retrieved_mix.final_health_hazards}"
        assert "H302" in retrieved_mix.final_health_hazards, \
            f"H302 chybí v {retrieved_mix.final_health_hazards}"
        assert "H332" in retrieved_mix.final_health_hazards, \
            f"H332 chybí v {retrieved_mix.final_health_hazards}"
        # GHS06 má přednost před GHS07
        assert "GHS06" in retrieved_mix.final_ghs_codes, \
            f"GHS06 chybí v {retrieved_mix.final_ghs_codes}"
