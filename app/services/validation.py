# app/services/validation.py
"""
Validační služba pro CLP Calculator.
Poskytuje pokročilou validaci a varování pro látky a směsi.
"""

from typing import List, Dict, Any, Optional
from app.models import Substance, Mixture


class ValidationMessage:
    """Třída pro reprezentaci validační zprávy."""
    
    LEVEL_ERROR = 'error'
    LEVEL_WARNING = 'warning'
    LEVEL_INFO = 'info'
    
    def __init__(self, level: str, field: str, message: str, suggestion: Optional[str] = None):
        self.level = level
        self.field = field
        self.message = message
        self.suggestion = suggestion
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level,
            'field': self.field,
            'message': self.message,
            'suggestion': self.suggestion
        }


# Mapování H-vět na požadované GHS kódy
H_TO_GHS_MAPPING = {
    # Akutní toxicita
    'H300': 'GHS06',  # Acute Tox 1,2 oral
    'H301': 'GHS06',  # Acute Tox 3 oral
    'H302': 'GHS07',  # Acute Tox 4 oral
    'H310': 'GHS06',  # Acute Tox 1,2 dermal
    'H311': 'GHS06',  # Acute Tox 3 dermal
    'H312': 'GHS07',  # Acute Tox 4 dermal
    'H330': 'GHS06',  # Acute Tox 1,2 inhal
    'H331': 'GHS06',  # Acute Tox 3 inhal
    'H332': 'GHS07',  # Acute Tox 4 inhal
    
    # Poleptání/podráždění
    'H314': 'GHS05',  # Skin Corr
    'H315': 'GHS07',  # Skin Irrit
    'H318': 'GHS05',  # Eye Dam
    'H319': 'GHS07',  # Eye Irrit
    
    # Senzibilizace
    'H317': 'GHS07',  # Skin Sens
    'H334': 'GHS08',  # Resp Sens
    
    # CMR
    'H340': 'GHS08',  # Muta 1
    'H341': 'GHS08',  # Muta 2
    'H350': 'GHS08',  # Carc 1
    'H351': 'GHS08',  # Carc 2
    'H360': 'GHS08',  # Repr 1
    'H361': 'GHS08',  # Repr 2
    
    # STOT
    'H370': 'GHS08',  # STOT SE 1
    'H371': 'GHS08',  # STOT SE 2
    'H372': 'GHS08',  # STOT RE 1
    'H373': 'GHS08',  # STOT RE 2
    'H335': 'GHS07',  # STOT SE 3 (resp irrit)
    'H336': 'GHS07',  # STOT SE 3 (narcotic)
    
    # Environmentální
    'H400': 'GHS09',  # Aquatic Acute 1
    'H410': 'GHS09',  # Aquatic Chronic 1
    'H411': 'GHS09',  # Aquatic Chronic 2
}


def validate_substance(substance: Substance) -> List[ValidationMessage]:
    """
    Validuje látku a vrací seznam varování/chyb.
    
    Args:
        substance: Instance Substance modelu
        
    Returns:
        Seznam ValidationMessage objektů
    """
    messages = []
    
    # 1. Kontrola H-vět vs GHS kódů
    if substance.health_h_phrases:
        h_phrases = [h.strip() for h in substance.health_h_phrases.split(',')]
        ghs_codes = substance.ghs_codes.split(',') if substance.ghs_codes else []
        ghs_codes = [g.strip() for g in ghs_codes]
        
        for h_phrase in h_phrases:
            if h_phrase in H_TO_GHS_MAPPING:
                required_ghs = H_TO_GHS_MAPPING[h_phrase]
                if required_ghs not in ghs_codes:
                    messages.append(ValidationMessage(
                        level=ValidationMessage.LEVEL_WARNING,
                        field='ghs_codes',
                        message=f"H-věta {h_phrase} vyžaduje GHS kód {required_ghs}",
                        suggestion=f"Přidejte {required_ghs} do pole GHS Kódy"
                    ))
    
    # 2. Kontrola ATE hodnot vs H-vět
    if substance.ate_oral:
        expected_h = _get_expected_h_from_ate(substance.ate_oral, 'oral')
        if expected_h and substance.health_h_phrases:
            h_phrases = [h.strip() for h in substance.health_h_phrases.split(',')]
            if expected_h not in h_phrases:
                messages.append(ValidationMessage(
                    level=ValidationMessage.LEVEL_INFO,
                    field='health_h_phrases',
                    message=f"ATE orální {substance.ate_oral} mg/kg odpovídá {expected_h}",
                    suggestion=f"Zvažte přidání {expected_h} do H-vět"
                ))
    
    # 3. Kontrola M-faktoru bez příslušné H-věty
    if substance.m_factor_acute and substance.m_factor_acute > 1:
        if not substance.env_h_phrases or 'H400' not in substance.env_h_phrases:
            messages.append(ValidationMessage(
                level=ValidationMessage.LEVEL_WARNING,
                field='m_factor_acute',
                message="M-faktor akutní je nastaven, ale chybí H400",
                suggestion="M-faktor akutní se používá pouze pro látky s H400 (Aquatic Acute 1)"
            ))
    
    if substance.m_factor_chronic and substance.m_factor_chronic > 1:
        if not substance.env_h_phrases or 'H410' not in substance.env_h_phrases:
            messages.append(ValidationMessage(
                level=ValidationMessage.LEVEL_WARNING,
                field='m_factor_chronic',
                message="M-faktor chronický je nastaven, ale chybí H410",
                suggestion="M-faktor chronický se používá pouze pro látky s H410 (Aquatic Chronic 1)"
            ))
    
    return messages


def validate_mixture(mixture: Mixture) -> List[ValidationMessage]:
    """
    Validuje směs a vrací seznam varování/chyb.
    
    Args:
        mixture: Instance Mixture modelu
        
    Returns:
        Seznam ValidationMessage objektů
    """
    messages = []
    
    # 1. Kontrola součtu koncentrací
    total_concentration = sum(comp.concentration for comp in mixture.components)
    
    if total_concentration > 100.01:
        messages.append(ValidationMessage(
            level=ValidationMessage.LEVEL_ERROR,
            field='components',
            message=f"Součet koncentrací přesahuje 100% ({total_concentration:.2f}%)",
            suggestion="Upravte koncentrace složek tak, aby součet byl max 100%"
        ))
    elif total_concentration < 99.0:
        missing = 100.0 - total_concentration
        messages.append(ValidationMessage(
            level=ValidationMessage.LEVEL_WARNING,
            field='components',
            message=f"Součet koncentrací je pouze {total_concentration:.2f}% (chybí {missing:.2f}%)",
            suggestion="Zkontrolujte, zda nejsou některé složky vynechány"
        ))
    
    # 2. Kontrola duplicitních složek
    substance_ids = [comp.substance_id for comp in mixture.components]
    if len(substance_ids) != len(set(substance_ids)):
        messages.append(ValidationMessage(
            level=ValidationMessage.LEVEL_ERROR,
            field='components',
            message="Směs obsahuje duplicitní složky",
            suggestion="Odstraňte nebo sloučte duplicitní složky"
        ))
    
    # 3. Kontrola prázdných složek
    if not mixture.components:
        messages.append(ValidationMessage(
            level=ValidationMessage.LEVEL_ERROR,
            field='components',
            message="Směs musí obsahovat alespoň jednu složku",
            suggestion="Přidejte složky do směsi"
        ))
    
    return messages


def check_duplicate_cas(cas_number: str, exclude_id: Optional[int] = None) -> Optional[Substance]:
    """
    Kontroluje, zda již existuje látka se stejným CAS číslem.
    
    Args:
        cas_number: CAS číslo k ověření
        exclude_id: ID látky, kterou chceme vyloučit (pro editaci)
        
    Returns:
        Substance pokud existuje duplicita, jinak None
    """
    if not cas_number:
        return None
    
    query = Substance.query.filter_by(cas_number=cas_number)
    if exclude_id:
        query = query.filter(Substance.id != exclude_id)
    
    return query.first()


def _get_expected_h_from_ate(ate_value: float, route: str) -> Optional[str]:
    """
    Určí očekávanou H-větu na základě ATE hodnoty.
    
    Args:
        ate_value: ATE hodnota
        route: Cesta expozice ('oral', 'dermal'). Poznámka: 'inhalation' zatím není implementováno.
        
    Returns:
        H-věta nebo None
    """
    if route == 'oral':
        if ate_value <= 5:
            return 'H300'
        elif ate_value <= 50:
            return 'H300'  # Cat 1 nebo 2
        elif ate_value <= 300:
            return 'H301'  # Cat 3
        elif ate_value <= 2000:
            return 'H302'  # Cat 4
    elif route == 'dermal':
        if ate_value <= 50:
            return 'H310'
        elif ate_value <= 200:
            return 'H310'  # Cat 1 nebo 2
        elif ate_value <= 1000:
            return 'H311'  # Cat 3
        elif ate_value <= 2000:
            return 'H312'  # Cat 4
    
    return None
