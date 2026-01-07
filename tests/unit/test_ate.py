import pytest
from app.services.clp.ate import (
    calculate_mixture_ate,
    classify_by_atemix,
    _determine_ate_category,
)
from app.models import Substance, Mixture, MixtureComponent


def test_calculate_mixture_ate_logic(app):
    """Test logiky výpočtu ATEmix bez potřeby databáze (pomocí mocků nebo reálných objektů v paměti)"""
    with app.app_context():
        s1 = Substance(name="S1", ate_oral=500)
        s2 = Substance(name="S2", ate_oral=1000)

        mix = Mixture(name="Test Mix")
        # Nasimulujeme komponenty
        c1 = MixtureComponent(substance=s1, concentration=50)
        c2 = MixtureComponent(substance=s2, concentration=50)
        mix.components = [c1, c2]

        results, logs = calculate_mixture_ate(mix)
        # 100 / (50/500 + 50/1000) = 100 / (0.1 + 0.05) = 100 / 0.15 = 666.67
        assert round(results["oral"], 2) == 666.67


def test_calculate_mixture_ate_with_unknown_logic(app):
    with app.app_context():
        s1 = Substance(name="S1", ate_oral=500)
        s2 = Substance(name="Unknown", ate_oral=None)  # Neznámá toxicita

        mix = Mixture(name="Test Mix Unknown")
        c1 = MixtureComponent(substance=s1, concentration=50)
        c2 = MixtureComponent(substance=s2, concentration=50)
        mix.components = [c1, c2]

        results, logs = calculate_mixture_ate(mix)
        # Aktuální implementace v ate.py ignoruje komponenty bez ATE.
        # Takže 100 / (50/500) = 1000.
        assert results["oral"] == 1000.0


def test_determine_ate_category():
    assert _determine_ate_category(5, "oral") == 1
    assert _determine_ate_category(50, "oral") == 2
    assert _determine_ate_category(300, "oral") == 3
    assert _determine_ate_category(2000, "oral") == 4
    assert _determine_ate_category(2001, "oral") == 5


def test_classify_by_atemix_integration():
    # Test integrace klasifikace z výsledků ATEmix
    # oral: 300.0 <= 300 -> Kat 3 -> H301
    # dermal: 1100.0 > 1000 a <= 2000 -> Kat 4 -> H312
    results = {"oral": 300.0, "dermal": 1100.0}
    hazards, ghs, logs = classify_by_atemix(results)

    assert "H301" in hazards
    assert "H312" in hazards
    assert "GHS06" in ghs  # Kvůli oral H301
    assert "GHS07" in ghs  # Kvůli dermal H312
