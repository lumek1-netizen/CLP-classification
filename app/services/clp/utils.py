"""
Utility funkce pro CLP služby.

Obsahuje pomocné funkce pro parsování a validaci dat z formulářů.
"""

from typing import Optional, Union


def get_float_or_none(form_data, field_name: str) -> Optional[float]:
    """
    Získá float hodnotu z formuláře nebo vrátí None.
    
    Podporuje české desetinné čárky (automaticky převede na tečky).
    
    Args:
        form_data: Data z request.form
        field_name: Název pole
        
    Returns:
        Float hodnota nebo None pokud je pole prázdné nebo nevalidní
        
    Examples:
        >>> get_float_or_none(request.form, 'ate_oral')
        500.0
        >>> get_float_or_none(request.form, 'empty_field')
        None
    """
    value = form_data.get(field_name, '').strip()
    
    if not value:
        return None
    
    try:
        # Nahradit desetinné čárky tečkami (pro české uživatele)
        value = value.replace(',', '.')
        return float(value)
    except ValueError:
        return None


def get_int_or_default(
    form_data, 
    field_name: str, 
    default: int = 1
) -> int:
    """
    Získá int hodnotu z formuláře nebo vrátí výchozí hodnotu.
    
    Args:
        form_data: Data z request.form
        field_name: Název pole
        default: Výchozí hodnota pokud je pole prázdné nebo nevalidní
        
    Returns:
        Int hodnota nebo default
        
    Examples:
        >>> get_int_or_default(request.form, 'm_factor_acute', 1)
        10
        >>> get_int_or_default(request.form, 'empty_field', 1)
        1
    """
    value = form_data.get(field_name, '').strip()
    
    if not value:
        return default
    
    try:
        return int(value)
    except ValueError:
        return default


