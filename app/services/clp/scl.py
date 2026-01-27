"""
Modul pro práci se Specifickými koncentračními limity (SCL).

Obsahuje parser pro SCL řetězce z databáze a vyhodnocovací logiku podmínek.
"""

from typing import Dict, List, Any, Optional
import re
from app.constants.clp import SCL_HAZARD_TO_H_CODE, SCL_HAZARD_TO_GHS_CODE





def _resolve_hazard_codes(hazard_category: str) -> tuple:
    """Vrátí H-větu a GHS kód pro danou CLP kategorii."""
    h_code = SCL_HAZARD_TO_H_CODE.get(hazard_category)
    ghs_code = SCL_HAZARD_TO_GHS_CODE.get(hazard_category)
    return h_code, ghs_code


def parse_scls(scls_string: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parsuje řetězec specifických koncentračních limitů (SCLs) do slovníku.
    
    Očekávaný formát: "Kategorie: podmínky; Kategorie: podmínky"
    Podmínky: ">= 5", "> 10.5", atd.
    
    Příklad: "Eye Irrit. 2: >= 10; Skin Irrit. 2: >= 10"
    
    Raises:
        ValueError: Pokud je formát nevalidní.
    """
    if not scls_string:
        return {}

    # Odstraňujeme agresivní normalizaci, pouze základní cleanup
    scls_string = scls_string.strip()
    # Povolit pouze běžné znaky, aby se zabránilo nesmyslům, ale to je možná moc striktní.
    # Spíše budeme parsovat a křičet, když to nesedí.
    
    parsed_scls = {}
    
    # Rozdělení na jednotlivé hazardy (oddělovač čárka, pokud není uvnitř závorky nebo uvozovek - zjednodušeně čárka)
    # Prozatím předpokládáme čárku jako oddělovač položek, pokud uživatel nepoužívá středníky na oddělení podmínek.
    # Ve specifikaci "Eye Irrit. 2: >= 10; < 20", je středník oddělovač podmínek.
    # Položky oddělujeme čárkou, např: "Cat1: >=1, Cat2: >=5"
    
    # Pro robustnější dělení (pokud by čárka byla v desetinném čísle):
    # Nahradíme desetinné čárky tečkami pro jistotu, to je bezpečné
    scls_string = re.sub(r'(\d+),(\d+)', r'\1.\2', scls_string)
    
    hazard_parts = [p.strip() for p in scls_string.split(",") if p.strip()]

    for hazard_part in hazard_parts:
        if ":" not in hazard_part and "=" not in hazard_part:
            raise ValueError(f"Neplatný formát SCL položky (chybí ':' nebo '='): '{hazard_part}'")

        if ":" in hazard_part:
            separator = ":"
        else:
            separator = "="
            
        hazard_category_raw, conditions_str = [
            s.strip() for s in hazard_part.split(separator, 1)
        ]
        
        # Validace názvu kategorie
        # Očistíme od H-kódů pokud je uživatel zadal (např. "Eye Irrit. 2 (H319)")
        hazard_category = re.sub(r'\s*\(?H\d{3}\)?', '', hazard_category_raw).strip()
        
        h_code, ghs_code = _resolve_hazard_codes(hazard_category)
        if not h_code:
            # Zkusíme s H-kódem v názvu, pokud by _resolve selhalo
            pass
            # Pokud stále nic, chyba
            # Ale dovolíme projít, pokud je to známá kategorie, jen my ji nemáme v mapě? 
            # Ne, chceme striktní režim.
            if hazard_category not in SCL_HAZARD_TO_H_CODE:
                 raise ValueError(f"Neznámá kategorie hazardu: '{hazard_category}'")

        condition_parts = [
            c.strip() for c in conditions_str.split(";") if c.strip()
        ]
        
        if not condition_parts:
             raise ValueError(f"Žádné podmínky pro kategorii '{hazard_category}'")

        if hazard_category not in parsed_scls:
            parsed_scls[hazard_category] = []

        for cond in condition_parts:
            # Odstranění %
            cond = cond.replace('%', '').strip()
            
            operator = None
            value_str = None
            
            # Detekce operátoru
            ops = [">=", "≥", "<=", "≤", ">", "<", "="]
            for op in ops:
                if cond.startswith(op):
                    operator = op
                    value_str = cond[len(op):].strip()
                    break
            
            # Pokud není operátor na začátku, ale je to jen číslo, předpokládáme >= (v souladu s běžnou praxí pro limity)
            if not operator:
                # Zkusíme jestli to je číslo
                try:
                    float(cond)
                    operator = ">="
                    value_str = cond
                except ValueError:
                    pass

            if not operator or not value_str:
                 raise ValueError(f"Nerozpoznaná podmínka '{cond}' pro '{hazard_category}'")

            # Normalizace operátorů pro interní logiku
            if operator == "≥": operator = ">="
            if operator == "≤": operator = "<="
            if operator == "=": operator = ">=" # Pro SCL se '=' obvykle chápe jako limit od

            try:
                value = float(value_str)
            except ValueError:
                raise ValueError(f"Neplatná číselná hodnota '{value_str}' v podmínce '{cond}'")
                
            parsed_scls[hazard_category].append(
                {
                    "op": operator,
                    "value": value,
                    "h_code": h_code,
                    "ghs": ghs_code,
                }
            )

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
