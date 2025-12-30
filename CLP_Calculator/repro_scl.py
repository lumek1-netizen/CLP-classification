
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.services.clp import parse_scls, classify_by_concentration_limits
from app.models import Mixture, MixtureComponent, Substance

# Mock db structures just enough for the service
class MockSubstance:
    def __init__(self, name, h_phrases, scl_limits=None):
        self.name = name
        self.health_h_phrases = h_phrases
        self.scl_limits = scl_limits
        self.env_h_phrases = None
        self.m_factor_acute = None
        self.m_factor_chronic = None

class MockComponent:
    def __init__(self, substance, concentration):
        self.substance = substance
        self.concentration = concentration

class MockMixture:
    def __init__(self, components):
        self.components = components

def test_scl_parsing():
    print("--- Test Parsing ---")
    # String from the user image (approximate)
    # "Specifický koncentrační limit: STOT SE 3; H335: C >= 5% Skin Corr. 1B; H314: C >= 25% ..."
    # Note: The prefix "Specifický koncentrační limit:" might be in the image text but possibly not in the DB field if user didn't paste it.
    # But let's assume worst case pasting: newlines, weird separators.
    
    raw_scl = """STOT SE 3; H335: C >= 5%
Skin Corr. 1B; H314: C >= 25%
Skin Irrit. 2; H315: 5% <= C < 25%
Eye Irrit. 2; H319: 5% <= C < 25%"""
    
    parsed = parse_scls(raw_scl)
    print(f"Raw Input:\n{raw_scl}")
    print(f"Parsed parsed keys: {list(parsed.keys())}")
    
    if 'Skin Corr. 1B' in parsed:
        print("✅ Skin Corr. 1B found")
        print(f"Conditions: {parsed['Skin Corr. 1B']}")
    else:
        print("❌ Skin Corr. 1B NOT found")

    # Test logic with this parsed SCL
    return parsed

def test_classification():
    print("\n--- Test Classification ---")
    # Mixture: Formaldehyde 13%
    # SCL for Skin Corr 1B >= 25%
    # GCL for Skin Corr 1 >= 5%
    # Expected: NOT Skin Corr 1/1B (H314). YES Skin Irrit 2 (H315).
    
    scl_text = "Skin Corr. 1B; H314: C >= 25%, Skin Irrit. 2; H315: 5% <= C < 25%"
    
    sub = MockSubstance("Formaldehyde", "H301, H311, H331, H314, H317, H341, H350", scl_text)
    mix = MockMixture([MockComponent(sub, 13.0)])
    
    hazards, ghs, logs = classify_by_concentration_limits(mix)
    
    print(f"Hazards: {hazards}")
    
    if 'H314' in hazards:
        print("❌ FAIL: H314 (Skin Corr) assigned! (Should be ignored due to SCL 25% > 13%)")
        # Print logs related to Skin Corr
        for log in logs:
            if 'Skin Corr' in log['step'] or 'H314' in log['result']:
                print(f"Original Log: {log}")
    else:
        print("✅ PASS: H314 NOT assigned.")

    if 'H315' in hazards:
        print("✅ PASS: H315 (Skin Irrit) assigned.")
    else:
        print("❌ FAIL: H315 NOT assigned (should be triggered by SCL range).")

if __name__ == "__main__":
    test_scl_parsing()
    test_classification()
