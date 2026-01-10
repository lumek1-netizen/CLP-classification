# app/services/export_service.py
"""
Export service pro exportování látek do CSV.
"""

import csv
import io
from typing import List, Optional
from app.models import Substance


def export_substances_to_csv(substance_ids: Optional[List[int]] = None) -> str:
    """
    Exportuje látky do CSV formátu.
    
    Args:
        substance_ids: None = všechny látky, list = vybrané látky
        
    Returns:
        CSV string
    """
    # Získání látek z databáze
    if substance_ids:
        substances = Substance.query.filter(Substance.id.in_(substance_ids)).all()
    else:
        substances = Substance.query.order_by(Substance.name).all()
    
    # Vytvoření CSV
    output = io.StringIO()
    
    # Definice sloupců
    fieldnames = [
        'name',
        'cas_number',
        'ghs_codes',
        'health_h_phrases',
        'env_h_phrases',
        'ate_oral',
        'ate_dermal',
        'ate_inhalation_vapours',
        'ate_inhalation_dusts_mists',
        'ate_inhalation_gases',
        'm_factor_acute',
        'm_factor_chronic',
        'scl_limits',
        'is_lact',
        'ed_hh_cat',
        'ed_env_cat',
        'is_pbt',
        'is_vpvb',
        'is_pmt',
        'is_vpvm',
        'has_ozone'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Zápis látek
    for substance in substances:
        row = {
            'name': substance.name or '',
            'cas_number': substance.cas_number or '',
            'ghs_codes': substance.ghs_codes or '',
            'health_h_phrases': substance.health_h_phrases or '',
            'env_h_phrases': substance.env_h_phrases or '',
            'ate_oral': substance.ate_oral if substance.ate_oral is not None else '',
            'ate_dermal': substance.ate_dermal if substance.ate_dermal is not None else '',
            'ate_inhalation_vapours': substance.ate_inhalation_vapours if substance.ate_inhalation_vapours is not None else '',
            'ate_inhalation_dusts_mists': substance.ate_inhalation_dusts_mists if substance.ate_inhalation_dusts_mists is not None else '',
            'ate_inhalation_gases': substance.ate_inhalation_gases if substance.ate_inhalation_gases is not None else '',
            'm_factor_acute': substance.m_factor_acute or 1,
            'm_factor_chronic': substance.m_factor_chronic or 1,
            'scl_limits': substance.scl_limits or '',
            'is_lact': '1' if substance.is_lact else '0',
            'ed_hh_cat': substance.ed_hh_cat if substance.ed_hh_cat is not None else '',
            'ed_env_cat': substance.ed_env_cat if substance.ed_env_cat is not None else '',
            'is_pbt': '1' if substance.is_pbt else '0',
            'is_vpvb': '1' if substance.is_vpvb else '0',
            'is_pmt': '1' if substance.is_pmt else '0',
            'is_vpvm': '1' if substance.is_vpvm else '0',
            'has_ozone': '1' if substance.has_ozone else '0',
        }
        writer.writerow(row)
    
    return output.getvalue()


def generate_csv_template() -> str:
    """
    Generuje prázdnou CSV šablonu s hlavičkou.
    
    Returns:
        CSV string s hlavičkou a příkladovými řádky
    """
    output = io.StringIO()
    
    fieldnames = [
        'name',
        'cas_number',
        'ghs_codes',
        'health_h_phrases',
        'env_h_phrases',
        'ate_oral',
        'ate_dermal',
        'ate_inhalation_vapours',
        'ate_inhalation_dusts_mists',
        'ate_inhalation_gases',
        'm_factor_acute',
        'm_factor_chronic',
        'scl_limits',
        'is_lact',
        'ed_hh_cat',
        'ed_env_cat',
        'is_pbt',
        'is_vpvb',
        'is_pmt',
        'is_vpvm',
        'has_ozone'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Příkladové řádky
    examples = [
        {
            'name': 'Ethanol',
            'cas_number': '64-17-5',
            'ghs_codes': 'GHS02, GHS07',
            'health_h_phrases': 'H225, H319',
            'env_h_phrases': '',
            'ate_oral': '7060',
            'ate_dermal': '15800',
            'ate_inhalation_vapours': '',
            'ate_inhalation_dusts_mists': '',
            'ate_inhalation_gases': '',
            'm_factor_acute': '1',
            'm_factor_chronic': '1',
            'scl_limits': '',
            'is_lact': '0',
            'ed_hh_cat': '',
            'ed_env_cat': '',
            'is_pbt': '0',
            'is_vpvb': '0',
            'is_pmt': '0',
            'is_vpvm': '0',
            'has_ozone': '0'
        },
        {
            'name': 'Formaldehyde',
            'cas_number': '50-00-0',
            'ghs_codes': 'GHS05, GHS06, GHS08',
            'health_h_phrases': 'H301, H311, H314, H317, H341, H350',
            'env_h_phrases': '',
            'ate_oral': '100',
            'ate_dermal': '300',
            'ate_inhalation_vapours': '',
            'ate_inhalation_dusts_mists': '',
            'ate_inhalation_gases': '',
            'm_factor_acute': '1',
            'm_factor_chronic': '1',
            'scl_limits': '',
            'is_lact': '0',
            'ed_hh_cat': '',
            'ed_env_cat': '',
            'is_pbt': '0',
            'is_vpvb': '0',
            'is_pmt': '0',
            'is_vpvm': '0',
            'has_ozone': '0'
        }
    ]
    
    for example in examples:
        writer.writerow(example)
    
    return output.getvalue()
