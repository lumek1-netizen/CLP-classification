# app/services/csv_parser.py
"""
CSV parser pro import látek do CLP Calculator.
"""

import csv
import io
import re
from typing import List, Dict, Tuple, Any, Optional


def validate_cas_number(cas: str) -> bool:
    """
    Validuje formát CAS čísla.
    
    Formát: XX-XX-X, XXX-XX-X, XXXX-XX-X, XXXXX-XX-X
    
    Args:
        cas: CAS číslo k validaci
        
    Returns:
        True pokud je formát platný
    """
    if not cas:
        return True  # CAS je volitelné
    
    # Pattern: 2-7 číslic, pomlčka, 2 číslice, pomlčka, 1 číslice
    pattern = r'^\d{2,7}-\d{2}-\d$'
    return bool(re.match(pattern, cas.strip()))


def validate_h_phrases(h_phrases: str, valid_phrases: set) -> Tuple[bool, List[str]]:
    """
    Validuje H-věty.
    
    Args:
        h_phrases: H-věty oddělené čárkou
        valid_phrases: Množina platných H-vět
        
    Returns:
        (is_valid, invalid_phrases)
    """
    if not h_phrases:
        return True, []
    
    phrases = [p.strip() for p in h_phrases.split(',')]
    invalid = [p for p in phrases if p and p not in valid_phrases]
    
    return len(invalid) == 0, invalid


def validate_ghs_codes(ghs_codes: str) -> Tuple[bool, List[str]]:
    """
    Validuje GHS kódy.
    
    Args:
        ghs_codes: GHS kódy oddělené čárkou
        
    Returns:
        (is_valid, invalid_codes)
    """
    if not ghs_codes:
        return True, []
    
    valid_ghs = {'GHS01', 'GHS02', 'GHS03', 'GHS04', 'GHS05', 'GHS06', 'GHS07', 'GHS08', 'GHS09'}
    codes = [c.strip() for c in ghs_codes.split(',')]
    invalid = [c for c in codes if c and c not in valid_ghs]
    
    return len(invalid) == 0, invalid


def parse_boolean(value: str) -> bool:
    """
    Parsuje boolean hodnotu z CSV.
    
    Args:
        value: Hodnota ('1', 'true', 'yes', '0', 'false', 'no')
        
    Returns:
        Boolean hodnota
    """
    if not value:
        return False
    
    value_lower = str(value).lower().strip()
    return value_lower in ('1', 'true', 'yes', 'ano')


def parse_float_safe(value: str) -> Optional[float]:
    """
    Bezpečně parsuje float hodnotu.
    
    Args:
        value: Hodnota k parsování
        
    Returns:
        Float nebo None
    """
    if not value or str(value).strip() == '':
        return None
    
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def parse_int_safe(value: str) -> Optional[int]:
    """
    Bezpečně parsuje int hodnotu.
    
    Args:
        value: Hodnota k parsování
        
    Returns:
        Int nebo None
    """
    if not value or str(value).strip() == '':
        return None
    
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def validate_csv_row(row: Dict[str, str], row_number: int, valid_h_phrases: set, valid_env_phrases: set) -> Tuple[bool, List[str], List[str]]:
    """
    Validuje jeden řádek CSV.
    
    Args:
        row: Slovník s daty řádku
        row_number: Číslo řádku (pro error reporting)
        valid_h_phrases: Množina platných zdravotních H-vět
        valid_env_phrases: Množina platných environmentálních H-vět
        
    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Povinné pole: name
    if not row.get('name', '').strip():
        errors.append(f"Řádek {row_number}: Chybí povinné pole 'name'")
    
    # Validace CAS
    cas = row.get('cas_number', '').strip()
    if cas and not validate_cas_number(cas):
        errors.append(f"Řádek {row_number}: Neplatný formát CAS čísla '{cas}'")
    
    # Validace H-vět
    health_h = row.get('health_h_phrases', '').strip()
    if health_h:
        is_valid, invalid = validate_h_phrases(health_h, valid_h_phrases)
        if not is_valid:
            warnings.append(f"Řádek {row_number}: Neznámé H-věty: {', '.join(invalid)}")
    
    env_h = row.get('env_h_phrases', '').strip()
    if env_h:
        is_valid, invalid = validate_h_phrases(env_h, valid_env_phrases)
        if not is_valid:
            warnings.append(f"Řádek {row_number}: Neznámé env H-věty: {', '.join(invalid)}")
    
    # Validace GHS kódů
    ghs = row.get('ghs_codes', '').strip()
    if ghs:
        is_valid, invalid = validate_ghs_codes(ghs)
        if not is_valid:
            errors.append(f"Řádek {row_number}: Neplatné GHS kódy: {', '.join(invalid)}")
    
    # Validace ATE hodnot (musí být čísla)
    for field in ['ate_oral', 'ate_dermal', 'ate_inhalation_vapours', 'ate_inhalation_dusts_mists', 'ate_inhalation_gases']:
        value = row.get(field, '').strip()
        if value and parse_float_safe(value) is None:
            errors.append(f"Řádek {row_number}: '{field}' musí být číslo, je '{value}'")
    
    # Validace M-faktorů (musí být celá čísla >= 1)
    for field in ['m_factor_acute', 'm_factor_chronic']:
        value = row.get(field, '').strip()
        if value:
            num = parse_int_safe(value)
            if num is None or num < 1:
                errors.append(f"Řádek {row_number}: '{field}' musí být celé číslo >= 1")
    
    return len(errors) == 0, errors, warnings


def parse_substances_csv(file_stream, valid_h_phrases: set, valid_env_phrases: set) -> Tuple[List[Dict], List[str], List[str]]:
    """
    Parsuje CSV soubor s látkami.
    
    Args:
        file_stream: File stream (z request.files)
        valid_h_phrases: Množina platných zdravotních H-vět
        valid_env_phrases: Množina platných environmentálních H-vět
        
    Returns:
        (parsed_substances, errors, warnings)
    """
    parsed_substances = []
    all_errors = []
    all_warnings = []
    
    try:
        # Streamované čtení bez načtení celého souboru do RAM
        # Předpokládáme UTF-8, pokud selže, zkusíme fallback (re-wrap streamu není triviální pro stream, 
        # ale pro upload file stream ve Flasku můžeme zkusit seek(0))
        
        file_stream.seek(0)
        wrapper = io.TextIOWrapper(file_stream, encoding='utf-8', errors='replace')
        
        # Parsování CSV přímo ze streamu
        # Použijeme csv.DictReader přímo na wrapper objektu
        reader = csv.DictReader(wrapper)
        
        if not reader.fieldnames:
            all_errors.append("CSV soubor je prázdný nebo nemá hlavičku")
            return [], all_errors, all_warnings
        
        # Kontrola povinných sloupců
        if 'name' not in reader.fieldnames:
            all_errors.append("CSV musí obsahovat sloupec 'name'")
            return [], all_errors, all_warnings
        
        # Parsování řádků
        for row_num, row in enumerate(reader, start=2):  # Start from 2 (1 is header)
            # Validace řádku
            is_valid, errors, warnings = validate_csv_row(row, row_num, valid_h_phrases, valid_env_phrases)
            
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            if is_valid:
                # Převod dat na správné typy
                substance_data = {
                    'name': row.get('name', '').strip(),
                    'cas_number': row.get('cas_number', '').strip() or None,
                    'ghs_codes': row.get('ghs_codes', '').strip() or None,
                    'health_h_phrases': row.get('health_h_phrases', '').strip() or None,
                    'env_h_phrases': row.get('env_h_phrases', '').strip() or None,
                    'ate_oral': parse_float_safe(row.get('ate_oral', '')),
                    'ate_dermal': parse_float_safe(row.get('ate_dermal', '')),
                    'ate_inhalation_vapours': parse_float_safe(row.get('ate_inhalation_vapours', '')),
                    'ate_inhalation_dusts_mists': parse_float_safe(row.get('ate_inhalation_dusts_mists', '')),
                    'ate_inhalation_gases': parse_float_safe(row.get('ate_inhalation_gases', '')),
                    'm_factor_acute': parse_int_safe(row.get('m_factor_acute', '')) or 1,
                    'm_factor_chronic': parse_int_safe(row.get('m_factor_chronic', '')) or 1,
                    'scl_limits': row.get('scl_limits', '').strip() or None,
                    'is_lact': parse_boolean(row.get('is_lact', '')),
                    'ed_hh_cat': parse_int_safe(row.get('ed_hh_cat', '')),
                    'ed_env_cat': parse_int_safe(row.get('ed_env_cat', '')),
                    'is_pbt': parse_boolean(row.get('is_pbt', '')),
                    'is_vpvb': parse_boolean(row.get('is_vpvb', '')),
                    'is_pmt': parse_boolean(row.get('is_pmt', '')),
                    'is_vpvm': parse_boolean(row.get('is_vpvm', '')),
                    'has_ozone': parse_boolean(row.get('has_ozone', '')),
                }
                
                parsed_substances.append(substance_data)
    
    except Exception as e:
        all_errors.append(f"Chyba při parsování CSV: {str(e)}")
    
    return parsed_substances, all_errors, all_warnings
