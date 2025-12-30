import sys
import os

# Přidání aktuálního adresáře do path
sys.path.append(os.getcwd())

from app.services.clp import parse_scls, evaluate_scl_condition, classify_by_concentration_limits

# --- Mock Classes ---
class MockSubstance:
    def __init__(self, name, health_h, scl_limits=None):
        self.name = name
        self.health_h_phrases = health_h
        self.scl_limits = scl_limits

class MockComponent:
    def __init__(self, substance, concentration):
        self.substance = substance
        self.concentration = concentration

class MockMixture:
    def __init__(self, components):
        self.components = components

def test_scl_parsing():
    print("--- Testování parsování SCL ---")
    
    # 1. Nový formát - jedna podmínka
    s1 = "Skin Corr. 1B: >= 25"
    p1 = parse_scls(s1)
    # print(f"Input: {s1} -> Parsed: {p1}")
    assert p1['Skin Corr. 1B'][0]['op'] == '>='
    assert p1['Skin Corr. 1B'][0]['value'] == 25.0
    
    # 2. Nový formát - rozmezí
    s2 = "Skin Irrit. 2: >= 5; < 25"
    p2 = parse_scls(s2)
    assert len(p2['Skin Irrit. 2']) == 2
    assert p2['Skin Irrit. 2'][1]['op'] == '<'
    assert p2['Skin Irrit. 2'][1]['value'] == 25.0
    
    # 3. Starý formát (zpětná kompatibilita)
    s3 = "Eye Irrit. 2=5"
    p3 = parse_scls(s3)
    assert p3['Eye Irrit. 2'][0]['op'] == '>='
    assert p3['Eye Irrit. 2'][0]['value'] == 5.0
    print("✅ Parsing OK")

def test_scl_evaluation():
    print("\n--- Testování vyhodnocování SCL podmínek ---")
    cond1 = [{'op': '>=', 'value': 25.0}]
    assert evaluate_scl_condition(30, cond1) == True
    assert evaluate_scl_condition(20, cond1) == False
    
    cond2 = [{'op': '>=', 'value': 5.0}, {'op': '<', 'value': 25.0}]
    assert evaluate_scl_condition(10, cond2) == True
    assert evaluate_scl_condition(25, cond2) == False
    print("✅ Evaluation OK")

def test_weighted_summation():
    print("\n--- Testování vážené sumace (Skin/Eye) ---")
    
    # Případ 1: Skin Corr 1 celkem >= 5% -> H314 (Skin Corr 1)
    # Látka A: Skin Corr 1A (3%), Látka B: Skin Corr 1B (3%) -> Suma 6%
    sub_a = MockSubstance("A", "H314") # Skin Corr 1A maps to H314
    sub_b = MockSubstance("B", "H314") 
    
    mix1 = MockMixture([
        MockComponent(sub_a, 3.0),
        MockComponent(sub_b, 3.0)
    ])
    
    hazards1, ghs1, log1 = classify_by_concentration_limits(mix1)
    print(f"Mix 1 (6% Corr): {hazards1}")
    assert 'H314' in hazards1
    
    # Případ 2: Skin Corr 1 < 5%, ale (10*Corr + Irrit) >= 10% -> H315 (Skin Irrit 2)
    # Látka A: Skin Corr 1 (0.8%), Látka C: Skin Irrit 2 (3%)
    # Výpočet: (10 * 0.8) + 3 = 8 + 3 = 11% >= 10% -> H315
    sub_c = MockSubstance("C", "H315") # Skin Irrit 2 maps to H315
    
    mix2 = MockMixture([
        MockComponent(sub_a, 0.8), # 0.8% Skin Corr 1
        MockComponent(sub_c, 3.0)  # 3.0% Skin Irrit 2
    ])
    
    hazards2, ghs2, log2 = classify_by_concentration_limits(mix2)
    print(f"Mix 2 (0.8% Corr + 3% Irrit): {hazards2}")
    assert 'H314' not in hazards2
    assert 'H315' in hazards2
    
    # Případ 3: Pod limitem
    # Látka A: Skin Corr 1 (0.5%), Látka C: Skin Irrit 2 (2%)
    # Výpočet: (10*0.5) + 2 = 5 + 2 = 7% < 10% -> Nic
    mix3 = MockMixture([
        MockComponent(sub_a, 0.5),
        MockComponent(sub_c, 2.0)
    ])
    
    hazards3, ghs3, log3 = classify_by_concentration_limits(mix3)
    print(f"Mix 3 (Low conc): {hazards3}")
    assert 'H314' not in hazards3
    assert 'H315' not in hazards3
    
    print("✅ Weighted Summation OK")

if __name__ == "__main__":
    try:
        test_scl_parsing()
        test_scl_evaluation()
        test_weighted_summation()
        print("\n🎉 Všechny testy proběhly úspěšně!")
    except AssertionError as e:
        print(f"\n❌ Test selhal! {e}")
        # sys.exit(1) # Neukončujeme, abychom viděli chybu v logu
        raise
    except Exception as e:
        print(f"\n❌ Došlo k chybě: {e}")
        raise
