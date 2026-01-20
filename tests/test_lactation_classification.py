
import pytest
from app.services.clp.health import classify_by_concentration_limits
from app.models import Substance, Mixture, MixtureComponent

def test_lactation_classification():
    """
    Testuje, zda se Laktace (H362) správně klasifikuje na základě health_h_phrases.
    """
    # 1. Vytvoření látky s H362
    substance = Substance(
        name="Lactation Substance",
        health_h_phrases="H362",
        env_h_phrases=""
    )
    
    # 2. Vytvoření směsi s koncentrací >= 0.3% (LACTATION_THRESHOLD_PERCENT)
    mixture = Mixture(name="Test Mixture")
    component = MixtureComponent(
        substance=substance,
        concentration=0.5  # 0.5% >= 0.3% limit
    )
    mixture.components.append(component)
    
    # 3. Klasifikace
    health_hazards, health_ghs, log_entries = classify_by_concentration_limits(mixture)
    
    # 4. Ověření
    assert "H362" in health_hazards
    assert any(entry['result'] == "H362" for entry in log_entries)
    print("\n✅ H362 Classification Test Passed!")

if __name__ == "__main__":
    test_lactation_classification()
