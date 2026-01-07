
import sys
import os

# Přidání aktuálního adresáře do path
sys.path.append(os.getcwd())

from app.services.clp.health import (
    classify_by_concentration_limits, 
    _get_cutoff_limit
)
from app.services.clp.env import classify_environmental_hazards
from app.services.clp.engine import get_signal_word

# --- Mock Classes ---
class MockSubstance:
    def __init__(self, name, health_h="", env_h="", scl_limits=None):
        self.name = name
        self.health_h_phrases = health_h
        self.env_h_phrases = env_h
        self.scl_limits = scl_limits
        self.m_factor_acute = 1
        self.m_factor_chronic = 1

class MockComponent:
    def __init__(self, substance, concentration):
        self.substance = substance
        self.concentration = concentration

class MockMixture:
    def __init__(self, components):
        self.components = components

def verify():
    results = []
    
    # 1. Test Cut-off (Ignorování pod 0.1% / 1%)
    results.append("--- 1. Test Cut-off ---")
    sub_carc = MockSubstance("CarcSub", health_h="H350") # Carc 1A -> cut-off 0.1%
    # Test pod cut-off
    mix_low = MockMixture([MockComponent(sub_carc, 0.05)])
    h, g, log = classify_by_concentration_limits(mix_low)
    results.append(f"Carc 1A (0.05%): {h} | Očekáváno: empty")
    
    # Test nad cut-off
    mix_high = MockMixture([MockComponent(sub_carc, 0.15)])
    h, g, log = classify_by_concentration_limits(mix_high)
    results.append(f"Carc 1A (0.15%): {h} | Očekáváno: {{'H350'}}")

    # 2. Test STOT SE 3 Aditivity (H335 + H336 >= 20%)
    results.append("\n--- 2. Test STOT SE 3 Aditivity ---")
    sub335 = MockSubstance("S335", health_h="H335")
    sub336 = MockSubstance("S336", health_h="H336")
    mix_stot = MockMixture([
        MockComponent(sub335, 10.0),
        MockComponent(sub336, 11.0)
    ])
    h, g, log = classify_by_concentration_limits(mix_stot)
    results.append(f"STOT 10% H335 + 11% H336: {h} | Očekáváno: {{'H335', 'H336'}}")

    # 3. Test H304 (Asp. Tox. 1)
    results.append("\n--- 3. Test H304 ---")
    sub304 = MockSubstance("S304", health_h="H304")
    mix_asp = MockMixture([MockComponent(sub304, 15.0)])
    h, g, log = classify_by_concentration_limits(mix_asp)
    results.append(f"Asp Tox 15%: {h} | Očekáváno: {{'H304'}}")

    # 4. Test Signálního slova (Nová logika podle H-vět)
    results.append("\n--- 4. Test Signálního slova ---")
    sig1 = get_signal_word({'GHS07'}, {'H302', 'H315'})
    results.append(f"H302+H315: {sig1} | Očekáváno: VAROVÁNÍ")
    
    sig2 = get_signal_word({'GHS05'}, {'H314'})
    results.append(f"H314: {sig2} | Očekáváno: NEBEZPEČÍ")
    
    sig3 = get_signal_word({'GHS08'}, {'H351'}) # Carc 2 -> Warning
    results.append(f"Carc 2 (H351): {sig3} | Očekáváno: VAROVÁNÍ")

    # Zápis výsledků do souboru
    with open("verification_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    print("Ověření dokončeno. Výsledky v verification_results.txt")

if __name__ == "__main__":
    verify()
