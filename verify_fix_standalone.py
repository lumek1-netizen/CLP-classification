import sqlite3
import os
import sys

# Přidání cesty k modulu app
sys.path.append(os.getcwd())

# Mock Mixture/Component pro HealthHazardClassifier pokud ho chceme použít přímo
class MockSubstance:
    def __init__(self, name, h, scl, ed=None, pbt=False):
        self.name = name
        self.health_h_phrases = h
        self.scl_limits = scl
        self.ed_hh_cat = ed
        self.is_pbt = pbt

class MockComponent:
    def __init__(self, sub, conc):
        self.substance = sub
        self.concentration = conc

class MockMixture:
    def __init__(self, ph=None):
        self.ph = ph
        self.components = []

from app.services.clp.health import HealthHazardClassifier

def verify_from_db(mixture_id):
    db_path = os.path.join("instance", "clp_calculator.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Načtení dat
    cursor.execute("SELECT name FROM mixture WHERE id=?", (mixture_id,))
    mix_row = cursor.fetchone()
    
    cursor.execute("""
        SELECT mc.concentration, s.name, s.health_h_phrases, s.scl_limits 
        FROM mixture_component mc
        JOIN substance s ON mc.substance_id = s.id
        WHERE mc.mixture_id = ?
    """, (mixture_id,))
    
    mock_mix = MockMixture()
    for row in cursor.fetchall():
        sub = MockSubstance(row['name'], row['health_h_phrases'], row['scl_limits'])
        comp = MockComponent(sub, row['concentration'])
        mock_mix.components.append(comp)
    
    conn.close()
    
    # Spuštění klasifikátoru (tentokrát už s opraveným kódem)
    classifier = HealthHazardClassifier(mock_mix)
    hazards, ghs, logs = classifier.classify()
    
    print(f"OVĚŘENÍ SMĚSI: {mix_row['name']}")
    print(f"Výsledné H-věty: {hazards}")
    
    if "H317" in hazards:
        print("SUCCESS: H317 je nyní správně přítomno!")
    else:
        print("FAIL: H317 stále chybí!")

if __name__ == "__main__":
    verify_from_db(5)
