from typing import Dict, List, Tuple, Optional
from app.models import Mixture
from app.constants.clp import ATE_LIMITS, ATE_POINT_ESTIMATES, ACUTE_TOXICITY_MAP

def calculate_mixture_ate(mixture: Mixture) -> Tuple[Dict[str, Optional[float]], List[Dict[str, str]]]:
    """Vypočítá ATEmix pro každou relevantní cestu expozice."""
    log_entries = []
    atemix_sums = {
        'oral': 0.0, 
        'dermal': 0.0, 
        'inhalation_gases': 0.0, 
        'inhalation_vapours': 0.0, 
        'inhalation_dusts_mists': 0.0
    }
    details = {k: [] for k in atemix_sums.keys()}

    for component in mixture.components:
        c = component.concentration
        substance = component.substance
        sub_name = substance.name
        h_phrases = substance.health_h_phrases if substance.health_h_phrases else ""

        # Helper function for points estimates
        def get_ate(val, route, h_phrases_str):
            if val is not None and val > 0:
                return val, "hodnota"
            if not h_phrases_str:
                return None, None
            
            h_to_cat = {
                'oral': {'H300': 2, 'H301': 3, 'H302': 4},
                'dermal': {'H310': 2, 'H311': 3, 'H312': 4},
                'gas': {'H330': 2, 'H331': 3, 'H332': 4},
                'vapour': {'H330': 2, 'H331': 3, 'H332': 4},
                'dust_mist': {'H330': 2, 'H331': 3, 'H332': 4}
            }
            
            for h, cat in h_to_cat.get(route, {}).items():
                if h in h_phrases_str:
                    return ATE_POINT_ESTIMATES.get(route, {}).get(cat), f"odhad ({h})"
            return None, None

        # Process routes
        routes_map = {
            'oral': ('oral', substance.ate_oral),
            'dermal': ('dermal', substance.ate_dermal),
            'inhalation_gases': ('gas', substance.ate_inhalation_gases),
            'inhalation_vapours': ('vapour', substance.ate_inhalation_vapours),
            'inhalation_dusts_mists': ('dust_mist', substance.ate_inhalation_dusts_mists)
        }

        for key, (route_type, val) in routes_map.items():
            ate_val, source = get_ate(val, route_type, h_phrases)
            if ate_val:
                atemix_sums[key] += c / ate_val
                details[key].append(f"{sub_name}: {c}% / {ate_val} ({source})")

    atemix_results = {}
    route_cz_names = {
        'oral': 'Orální', 'dermal': 'Dermální', 
        'inhalation_gases': 'Inhalační (plyny)', 
        'inhalation_vapours': 'Inhalační (páry)', 
        'inhalation_dusts_mists': 'Inhalační (prach/mlha)'
    }

    for route, sum_ci_atei in atemix_sums.items():
        if sum_ci_atei > 0:
            val = 100.0 / sum_ci_atei
            atemix_results[route] = val
            route_cz = route_cz_names.get(route, route)
            calculation_detail = " + ".join(details[route])
            log_entries.append({
                "step": f"Výpočet ATEmix - {route_cz}",
                "detail": f"Vzorec: 100 / ({calculation_detail})",
                "result": f"ATEmix = {val:.2f}"
            })
        else:
            atemix_results[route] = None
            
    return atemix_results, log_entries

def _determine_ate_category(ate_value: float, route: str) -> int:
    """Určí kategorii akutní toxicity (1-4). 5 pro neklasifikováno."""
    norm_route = route
    if 'oral' in route: norm_route = 'oral'
    elif 'dermal' in route: norm_route = 'dermal'
    elif 'gas' in route: norm_route = 'gas'
    elif 'vapour' in route: norm_route = 'vapour'
    elif 'dust' in route or 'mist' in route: norm_route = 'dust_mist'

    limits = ATE_LIMITS.get(norm_route, [])
    for i, limit in enumerate(limits):
        if ate_value <= limit:
            return i + 1
    return 5

def classify_by_atemix(atemix_results: Dict[str, Optional[float]]) -> Tuple[set, set, List[Dict[str, str]]]:
    """Přiřadí H-věty a GHS kódy na základě ATEmix hodnot."""
    atemix_hazards = set()
    atemix_ghs = set()
    log_entries = []
    
    route_cz_names = {
        'oral': 'Orální', 'dermal': 'Dermální', 
        'inhalation_gases': 'Inhalační (plyny)', 
        'inhalation_vapours': 'Inhalační (páry)', 
        'inhalation_dusts_mists': 'Inhalační (prach/mlha)'
    }

    for route, atemix_value in atemix_results.items():
        if atemix_value is None:
            continue
        
        category = _determine_ate_category(atemix_value, route)
        route_cz = route_cz_names.get(route, route)
        log_msg = f"Hodnota {atemix_value:.3f} spadá do Kategorie {category}"
        
        if category < 5:
            hazard_info = ACUTE_TOXICITY_MAP.get(category)
            if hazard_info:
                ghs_code = hazard_info['ghs']
                h_code_suffix = {1: 0, 2: 0, 3: 1, 4: 2}.get(category)
                
                h_code = None
                if route == 'oral': h_code = f'H30{h_code_suffix}'
                elif route == 'dermal': h_code = f'H31{h_code_suffix}'
                elif route.startswith('inhalation'): h_code = f'H33{h_code_suffix}'
                
                if h_code and ghs_code:
                    atemix_hazards.add(h_code)
                    atemix_ghs.add(ghs_code)
                    log_msg += f" -> Přiřazeno {h_code}, {ghs_code}"
        else:
            log_msg += " -> Neklasifikováno"
            
        log_entries.append({
            "step": f"Klasifikace ATE - {route_cz}",
            "detail": log_msg,
            "result": "OK"
        })
    
    return atemix_hazards, atemix_ghs, log_entries
