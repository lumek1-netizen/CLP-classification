from typing import Dict, List, Tuple, Set
from app.models import Mixture

def classify_environmental_hazards(mixture: Mixture) -> Tuple[Set, Set, List[Dict[str, str]]]:
    """Provádí klasifikaci nebezpečnosti pro životní prostředí."""
    env_hazards = set()
    env_ghs = set()
    log_entries = []
    
    sum_acute_1 = 0.0
    sum_chronic_1 = 0.0
    contributors_acute_1 = []
    contributors_chronic_1 = []
    
    sum_chronic_2 = 0.0
    sum_chronic_3 = 0.0
    contributors_chronic_2 = []
    contributors_chronic_3 = []
    
    for component in mixture.components:
        substance = component.substance
        concentration = component.concentration
        sub_name = substance.name
        
        if substance.env_h_phrases:
            env_h_codes = [h.strip() for h in substance.env_h_phrases.split(',')]
            for h_code in env_h_codes:
                if h_code == 'H400':
                    if concentration < 0.1: continue
                    m_factor = substance.m_factor_acute or 1
                    sum_acute_1 += concentration * m_factor
                    contributors_acute_1.append(f"{sub_name} ({concentration}% x M{m_factor})")
                elif h_code == 'H410':
                    if concentration < 0.1: continue
                    m_factor = substance.m_factor_chronic or 1
                    sum_chronic_1 += concentration * m_factor
                    contributors_chronic_1.append(f"{sub_name} ({concentration}% x M{m_factor})")
                elif h_code == 'H411':
                    if concentration < 1.0: continue
                    sum_chronic_2 += concentration
                    contributors_chronic_2.append(f"{sub_name} ({concentration}%)")
                elif h_code == 'H412':
                    if concentration < 1.0: continue
                    sum_chronic_3 += concentration
                    contributors_chronic_3.append(f"{sub_name} ({concentration}%)")
    
    if sum_acute_1 >= 25:
        env_hazards.add('H400')
        env_ghs.add('GHS09')
        log_entries.append({"step": "Aquatic Acute 1", "detail": f"Součet = {sum_acute_1} >= 25", "result": "H400"})
    
    if sum_chronic_1 >= 25:
        env_hazards.add('H410')
        env_ghs.add('GHS09')
        log_entries.append({"step": "Aquatic Chronic 1", "detail": f"Součet = {sum_chronic_1} >= 25", "result": "H410"})
        
    val_c2 = (10 * sum_chronic_1) + sum_chronic_2
    if val_c2 >= 25:
        if 'H410' not in env_hazards:
            env_hazards.add('H411')
            env_ghs.add('GHS09')
        log_entries.append({"step": "Aquatic Chronic 2", "detail": f"Vážený součet = {val_c2} >= 25", "result": "H411"})
        
    val_c3 = (100 * sum_chronic_1) + (10 * sum_chronic_2) + sum_chronic_3
    if val_c3 >= 25:
        if 'H410' not in env_hazards and 'H411' not in env_hazards:
            env_hazards.add('H412')
        log_entries.append({"step": "Aquatic Chronic 3", "detail": f"Vážený součet = {val_c3} >= 25", "result": "H412"})
    
    return env_hazards, env_ghs, log_entries
