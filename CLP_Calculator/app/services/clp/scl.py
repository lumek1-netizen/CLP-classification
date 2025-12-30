from typing import Dict, List, Any, Optional
from app.constants.clp import SCL_HAZARD_TO_H_CODE, SCL_HAZARD_TO_GHS_CODE

def _resolve_hazard_codes(hazard_category: str) -> tuple:
    """Vrátí H-větu a GHS kód pro danou CLP kategorii."""
    h_code = SCL_HAZARD_TO_H_CODE.get(hazard_category)
    ghs_code = SCL_HAZARD_TO_GHS_CODE.get(hazard_category)
    return h_code, ghs_code

def parse_scls(scls_string: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Parsuje řetězec specifických koncentračních limitů (SCLs) do slovníku."""
    if not scls_string:
        return {}
    
    parsed_scls = {}
    hazard_parts = [p.strip() for p in scls_string.split(',') if p.strip()]
    
    for hazard_part in hazard_parts:
        if ':' in hazard_part:
            hazard_category, conditions_str = [s.strip() for s in hazard_part.split(':', 1)]
            condition_parts = [c.strip() for c in conditions_str.split(';') if c.strip()]
            h_code, ghs_code = _resolve_hazard_codes(hazard_category)
            
            if not h_code or not ghs_code:
                continue
            
            if hazard_category not in parsed_scls:
                parsed_scls[hazard_category] = []
            
            for cond in condition_parts:
                operator = None
                value_str = None
                for op in ['>=', '<=', '>', '<']:
                    if op in cond:
                        parts = cond.split(op, 1)
                        if len(parts) == 2:
                            operator = op
                            value_str = parts[1].strip()
                            break
                
                if operator and value_str:
                    try:
                        value = float(value_str)
                        parsed_scls[hazard_category].append({
                            'op': operator,
                            'value': value,
                            'h_code': h_code,
                            'ghs': ghs_code
                        })
                    except ValueError:
                        continue
        
        elif '=' in hazard_part:
            hazard_category, value_str = [s.strip() for s in hazard_part.split('=', 1)]
            try:
                value = float(value_str)
                h_code, ghs_code = _resolve_hazard_codes(hazard_category)
                if h_code and ghs_code:
                    if hazard_category not in parsed_scls:
                        parsed_scls[hazard_category] = []
                    parsed_scls[hazard_category].append({
                        'op': '>=',
                        'value': value,
                        'h_code': h_code,
                        'ghs': ghs_code
                    })
            except ValueError:
                continue
    
    return parsed_scls

def format_scls_for_db(parsed_scls: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
    """Formátuje strukturovaný SCL slovník zpět do DB stringu."""
    if not parsed_scls:
        return None
    
    parts = []
    for hazard, conditions in parsed_scls.items():
        if conditions:
            cond_strs = [f"{c['op']} {c['value']:.3f}" for c in conditions]
            parts.append(f"{hazard}: {'; '.join(cond_strs)}")
    
    return ', '.join(parts)

def evaluate_scl_condition(concentration: float, conditions: List[Dict[str, Any]]) -> bool:
    """Vyhodnotí, zda koncentrace splňuje SCL podmínky (AND logika)."""
    for cond in conditions:
        op = cond['op']
        val = cond['value']
        if op == '>=' and not (concentration >= val): return False
        if op == '>' and not (concentration > val): return False
        if op == '<=' and not (concentration <= val): return False
        if op == '<' and not (concentration < val): return False
    return True
