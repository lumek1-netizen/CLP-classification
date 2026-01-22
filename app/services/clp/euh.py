from typing import Set, List, Dict, Tuple, Optional
from app.models import Mixture
from app.constants.clp import EUH_PHRASES

def classify_euh_phrases(mixture: Mixture, health_hazards: Set[str], env_hazards: Set[str], components: Optional[List] = None) -> Tuple[Set[str], List[Dict[str, str]]]:
    """
    Vyhodnotí doplňkové EUH věty na základě obsahu látek a výsledné klasifikace.
    """
    euh_codes = set()
    log_entries = []
    
    # Použít předaný seznam komponent nebo ten z mixture
    calc_components = components if components is not None else mixture.components
    
    # 1. EUH208 - Obsahuje (název senzibilizující látky). Může vyvolat alergickou reakci.
    sensitizers_limit_trigger = []
    
    for component in calc_components:
        sub = component.substance
        conc = component.concentration
        h_phrases = sub.health_h_phrases or ""
        
        # Skin Sens nebo Resp Sens
        if "H317" in h_phrases or "H334" in h_phrases:
            if "H317" not in health_hazards and "H334" not in health_hazards:
                trigger = 0.1 
                if "1A" in h_phrases:
                    trigger = 0.01
                
                if conc >= trigger:
                    sensitizers_limit_trigger.append(sub.name)

    if sensitizers_limit_trigger:
        euh_codes.add("EUH208")
        names_str = ", ".join(sensitizers_limit_trigger)
        log_entries.append({
            "step": "EUH208",
            "detail": f"Obsahuje senzibilizátory pod limitem klasifikace: {names_str}",
            "result": "EUH208"
        })

    # 2. Nové EUH věty pro ED, PBT, PMT
    ed_hh1_names = []
    ed_hh2_names = []
    pbt_names = []
    pmt_names = []
    
    for component in calc_components:
        sub = component.substance
        conc = component.concentration
        
        if conc >= 0.1:
            if getattr(sub, 'ed_hh_cat', None) == 1: ed_hh1_names.append(sub.name)
            if getattr(sub, 'ed_hh_cat', None) == 2: ed_hh2_names.append(sub.name)
            if getattr(sub, 'is_pbt', False) or getattr(sub, 'is_vpvb', False): pbt_names.append(sub.name)
            if getattr(sub, 'is_pmt', False) or getattr(sub, 'is_vpvm', False): pmt_names.append(sub.name)

    if ed_hh1_names: euh_codes.add("EUH430")
    if ed_hh2_names: euh_codes.add("EUH431")
    if pbt_names: euh_codes.add("EUH450")
    if pmt_names: euh_codes.add("EUH451")

    # 3. EUH210 - Bezpečnostní list na vyžádání
    if not health_hazards and not env_hazards:
        has_dangerous_sub = any(c.concentration >= 1.0 for c in calc_components)
        if has_dangerous_sub:
            euh_codes.add("EUH210")

    return euh_codes, log_entries
