from typing import Dict, List, Tuple, Set, Any, Optional

# Mock constants for headless test
SKIN_CORROSION_THRESHOLD_PERCENT = 5.0
SKIN_IRRITATION_THRESHOLD_PERCENT = 10.0
EYE_DAMAGE_THRESHOLD_PERCENT = 3.0
EYE_IRRITATION_THRESHOLD_PERCENT = 10.0
STOT_SE3_THRESHOLD_PERCENT = 20.0
GENERAL_CUTOFF_PERCENT = 1.0
SENSITISATION_CUTOFF_PERCENT = 0.1
CMR_CUTOFF_PERCENT = 0.1
STOT_CATEGORY_1_CUTOFF_PERCENT = 0.1

STANDARD_CONCENTRATION_LIMITS = {
    "Skin Sens. 1": {"cl": 1.0},
    "Carc. 1B": {"cl": 0.1},
}

SCL_HAZARD_TO_H_CODE = {
    "Skin Corr. 1": "H314",
    "Skin Irrit. 2": "H315",
    "Eye Dam. 1": "H318",
    "Eye Irrit. 2": "H319",
    "Skin Sens. 1": "H317",
    "Carc. 1B": "H350",
}

HAZARD_GROUPS = {
    "Skin": ["Skin Corr. 1", "Skin Irrit. 2"],
    "Eye": ["Eye Dam. 1", "Eye Irrit. 2"],
    "SkinSens": ["Skin Sens. 1"],
    "Carc": ["Carc. 1B"],
}

CAT_TO_GROUP = {c: grp for grp, cats in HAZARD_GROUPS.items() for c in cats}
H_CODE_TO_GROUPS = {}
for cat, h_code in SCL_HAZARD_TO_H_CODE.items():
    if cat in CAT_TO_GROUP:
        grp = CAT_TO_GROUP[cat]
        H_CODE_TO_GROUPS.setdefault(h_code, set()).add(grp)

class Component:
    def __init__(self, name, conc, h):
        self.substance = Substance(name, h)
        self.concentration = conc

class Substance:
    def __init__(self, name, h):
        self.name = name
        self.health_h_phrases = h
        self.scl_limits = None

class Mixture:
    def __init__(self, ph=None):
        self.ph = ph
        self.components = []

class MiniClassifier:
    def __init__(self, components):
        self.components = components
        self.hazard_totals = {}
        self.health_hazards = set()

    def _add_contribution(self, category, conc, name, note="", forced_by_scl=False):
        if category not in self.hazard_totals:
            self.hazard_totals[category] = {"total": 0.0, "contributors": []}
        self.hazard_totals[category]["total"] += conc
        self.hazard_totals[category]["contributors"].append(f"{name} ({conc}%)")

    def classify(self):
        for comp in self.components:
            h_codes = [h.strip() for h in comp.substance.health_h_phrases.split(",")]
            for h_code in h_codes:
                group = list(H_CODE_TO_GROUPS.get(h_code, []))[0]
                target_cat = h_code # Simplified mapping
                # Fallback to cat name if we wanted to be precise
                for k,v in SCL_HAZARD_TO_H_CODE.items():
                    if v == h_code: target_cat = k
                
                limit = STANDARD_CONCENTRATION_LIMITS.get(target_cat, {}).get("cl", 1.0)
                if comp.concentration >= limit:
                     self._add_contribution(target_cat, comp.concentration, comp.substance.name)
        
        self._evaluate_generic_hazards()
        return self.health_hazards

    def _evaluate_generic_hazards(self):
        # BUG HERE: "Skin" prefix captures "Skin Sens. 1"
        excluded_prefixes = ("Skin", "Eye", "Aquatic", "STOT SE 3")
        print(f"DEBUG: hazard_totals keys = {list(self.hazard_totals.keys())}")
        for cat, data in self.hazard_totals.items():
            if cat.startswith(excluded_prefixes):
                print(f"DEBUG: Skipping {cat} because it starts with excluded prefix")
                continue
            
            h_code = SCL_HAZARD_TO_H_CODE.get(cat)
            if h_code:
                self.health_hazards.add(h_code)

if __name__ == "__main__":
    # Test with Formaldehyde 10% (H317, H350)
    comps = [Component("Formaldehyd", 10.0, "H317,H350")]
    classifier = MiniClassifier(comps)
    hazards = classifier.classify()
    print(f"RESULT: {hazards}")
    if "H317" not in hazards:
        print("FAIL: H317 is missing!")
    if "H350" in hazards:
        print("PASS: H350 is present.")
