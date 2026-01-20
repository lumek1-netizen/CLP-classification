
import pytest
from app.services.clp.env import classify_environmental_hazards
from app.models import Substance, Mixture, MixtureComponent

def test_ozone_classification():
    """
    Testuje, zda se Ozonová vrstva (H420) správně klasifikuje na základě env_h_phrases.
    """
    # 1. Vytvoření látky s H420
    substance = Substance(
        name="Ozone Substance",
        health_h_phrases="",
        env_h_phrases="H420"
    )
    
    # 2. Vytvoření směsi s koncentrací >= 0.1% (hranice pro ozon)
    mixture = Mixture(name="Test Mixture Ozone")
    component = MixtureComponent(
        substance=substance,
        concentration=0.5  # 0.5% >= 0.1% limit
    )
    mixture.components.append(component)
    
    # 3. Klasifikace
    env_hazards, env_ghs, log_entries = classify_environmental_hazards(mixture)
    
    # 4. Ověření
    # U ozonu se standardně přidává H420 do hazards, pokud je v ozone_names
    # V classify_environmental_hazards je logika na konci, která to přidává
    # Musím se podívat do zbytku env.py, abych viděl, zda se to přidává do env_hazards
    
    # Poznámka: v logice env.py se plní ozone_names, pak se to asi vyhodnocuje
    # Zkontrolujeme výsledek
    assert "H420" in env_hazards
    assert any(entry['result'] == "H420" for entry in log_entries)
    print("\n✅ H420 Classification Test Passed!")

if __name__ == "__main__":
    test_ozone_classification()
