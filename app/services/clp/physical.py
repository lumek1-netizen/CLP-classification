from typing import List, Dict, Tuple, Optional
from app.constants.clp import PhysicalState

def evaluate_flammable_liquids(
    flash_point: Optional[float], boiling_point: Optional[float]
) -> Tuple[set, set, List[Dict[str, str]]]:
    """
    Evaluates Flammable Liquids (H224, H225, H226) based on Flash Point and Boiling Point.
    Returns: (hazards, ghs_codes, log_entries)
    """
    hazards = set()
    ghs_codes = set()
    log_entries = []

    if flash_point is None:
        return hazards, ghs_codes, log_entries
    
    # Logic based on CLP Table 2.6.1
    # Cat 1: FP < 23°C and BP <= 35°C -> H224
    # Cat 2: FP < 23°C and BP > 35°C -> H225
    # Cat 3: FP >= 23°C and FP <= 60°C -> H226
    
    category = None
    
    if flash_point < 23:
        if boiling_point is not None and boiling_point <= 35:
            category = 1
        elif boiling_point is not None and boiling_point > 35:
            category = 2
        elif boiling_point is None:
             # Worst case assumption if BP is missing but FP is low? 
             # Or just warn? For now warn and do not classify distincly?
             # Let's default to Cat 1 (most severe) if unknown? No, fail safe means warn.
             log_entries.append({
                 "step": "Fyzikální nebezpečnost - Hořlavé kapaliny",
                 "detail": f"Bod vzplanutí {flash_point}°C < 23°C, ale chybí bod varu. Nelze rozhodnout mezi Cat 1 a Cat 2.",
                 "result": "Neklasifikováno (chybí data)"
             })
             return hazards, ghs_codes, log_entries
    elif 23 <= flash_point <= 60:
        category = 3

    if category == 1:
        hazards.add("H224")
        ghs_codes.add("GHS02")
        log_entries.append({
            "step": "Fyzikální nebezpečnost - Hořlavé kapaliny",
            "detail": f"Bod vzplanutí {flash_point}°C, Bod varu {boiling_point}°C -> Kategorie 1",
            "result": "H224, GHS02"
        })
    elif category == 2:
        hazards.add("H225")
        ghs_codes.add("GHS02")
        log_entries.append({
             "step": "Fyzikální nebezpečnost - Hořlavé kapaliny",
             "detail": f"Bod vzplanutí {flash_point}°C, Bod varu {boiling_point}°C -> Kategorie 2",
             "result": "H225, GHS02"
        })
    elif category == 3:
        hazards.add("H226")
        ghs_codes.add("GHS02")
        log_entries.append({
             "step": "Fyzikální nebezpečnost - Hořlavé kapaliny",
             "detail": f"Bod vzplanutí {flash_point}°C -> Kategorie 3",
             "result": "H226, GHS02"
        })
    else:
         log_entries.append({
             "step": "Fyzikální nebezpečnost - Hořlavé kapaliny",
             "detail": f"Bod vzplanutí {flash_point}°C > 60°C",
             "result": "Mimo kriteria"
        })
        
    return hazards, ghs_codes, log_entries
