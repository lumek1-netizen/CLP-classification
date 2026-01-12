from typing import Dict, List, Any, Optional
import re
from app.constants.clp import SCL_HAZARD_TO_H_CODE, SCL_HAZARD_TO_GHS_CODE


def _normalize_scl_input(scls_string: str) -> str:
    """
    Normalizuje uživatelský vstup SCL do standardního formátu.
    
    Podporuje:
    - Nové řádky jako oddělovače kategorií
    - Symboly % (odstraní se)
    - Desetinné čárky (převede na tečky)
    - H-kódy za středníkem (odstraní se)
    - Rozsahy (např. "1 - 30" → extrahuje dolní limit)
    - Multi-line formát (kategorie na jednom řádku, hodnota na dalším)
    """
    if not scls_string:
        return ""
    
    # Krok 1: Jednoduchá předzpracování  
    # Odstranit H-kódy (např. "; H319")
    normalized = re.sub(r';\s*H\d{3}', '', scls_string)
    # Odstranit %
    normalized = normalized.replace('%', '')
    
    # Podpora pro unicode operátory
    normalized = normalized.replace('≤', '<=').replace('≥', '>=')
    
    # Převést desetinné čárky na tečky v číslech (včetně mezer kolem čárky)
    normalized = re.sub(r'(\d+)\s*,\s*(\d+)', r'\1.\2', normalized)
    
    # Krok 2: Zpracovat řádky
    # Rozdělit na řádky a odstranit prázdné
    lines = [line.strip() for line in normalized.split('\n') if line.strip()]
    
    # Kor 3: Zpracovat multi-line formát (kategorie + hodnota na dalším řádku)
    # Algoritmus: pokud řádek začíná operátorem nebo číslem, je to hodnota pro předchozí kategorii
    result_parts = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Je to kategorie (obsahuje písmena) nebo hodnota (začíná operátorem/číslem)?
        is_value_line = re.match(r'^\s*([><<=]{1,2})?\s*\d', line)
        
        if is_value_line and result_parts:
            # Toto je hodnota pro předchozí kategorii
            # Zpracovat rozsahy
            value = _process_range_in_value(line)
            # Přidat k poslední kategorii
            result_parts[-1] = f"{result_parts[-1]}: {value}"
        elif not is_value_line:
            # Toto je kategorie
            result_parts.append(line)
        
        i += 1
    
    # Krok 4: Spojit částečky čárkami
    normalized = ', '.join(result_parts)
    
    return normalized


def _process_range_in_value(value_str: str) -> str:
    """Zpracuje rozsahy v hodnotě (např. '1 - 30' → '>= 1')"""
    def process_range(match):
        operator = match.group(1) or '>='
        lower_value = match.group(2).strip()
        return f"{operator} {lower_value}"
    
    # Regex pro rozsahy
    processed = re.sub(
        r'([><<=]{1,2})?\s*(\d+(?:\.\d+)?)\s+\-\s+(\d+(?:\.\d+)?)',
        process_range,
        value_str
    )
    
    return processed.strip()


def _resolve_hazard_codes(hazard_category: str) -> tuple:
    """Vrátí H-větu a GHS kód pro danou CLP kategorii."""
    h_code = SCL_HAZARD_TO_H_CODE.get(hazard_category)
    ghs_code = SCL_HAZARD_TO_GHS_CODE.get(hazard_category)
    return h_code, ghs_code


def parse_scls(scls_string: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Parsuje řetězec specifických koncentračních limitů (SCLs) do slovníku."""
    if not scls_string:
        return {}

    # Normalizace vstupu pro podporu uživatelsky přívětivých formátů
    scls_string = _normalize_scl_input(scls_string)
    
    parsed_scls = {}
    hazard_parts = [p.strip() for p in scls_string.split(",") if p.strip()]

    for hazard_part in hazard_parts:
        if ":" in hazard_part:
            hazard_category, conditions_str = [
                s.strip() for s in hazard_part.split(":", 1)
            ]
            condition_parts = [
                c.strip() for c in conditions_str.split(";") if c.strip()
            ]
            h_code, ghs_code = _resolve_hazard_codes(hazard_category)

            if not h_code or not ghs_code:
                continue

            if hazard_category not in parsed_scls:
                parsed_scls[hazard_category] = []

            for cond in condition_parts:
                operator = None
                value_str = None
                for op in [">=", "<=", ">", "<"]:
                    if op in cond:
                        parts = cond.split(op, 1)
                        if len(parts) == 2:
                            operator = op
                            value_str = parts[1].strip()
                            break

                if operator and value_str:
                    try:
                        value = float(value_str)
                        parsed_scls[hazard_category].append(
                            {
                                "op": operator,
                                "value": value,
                                "h_code": h_code,
                                "ghs": ghs_code,
                            }
                        )
                    except ValueError:
                        continue

        elif "=" in hazard_part:
            hazard_category, value_str = [s.strip() for s in hazard_part.split("=", 1)]
            try:
                value = float(value_str)
                h_code, ghs_code = _resolve_hazard_codes(hazard_category)
                if h_code and ghs_code:
                    if hazard_category not in parsed_scls:
                        parsed_scls[hazard_category] = []
                    parsed_scls[hazard_category].append(
                        {"op": ">=", "value": value, "h_code": h_code, "ghs": ghs_code}
                    )
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

    return ", ".join(parts)


def evaluate_scl_condition(
    concentration: float, conditions: List[Dict[str, Any]]
) -> bool:
    """Vyhodnotí, zda koncentrace splňuje SCL podmínky (AND logika)."""
    for cond in conditions:
        op = cond["op"]
        val = cond["value"]
        if op in [">=", "≥"] and not (concentration >= val):
            return False
        if op == ">" and not (concentration > val):
            return False
        if op in ["<=", "≤"] and not (concentration <= val):
            return False
        if op == "<" and not (concentration < val):
            return False
    return True
