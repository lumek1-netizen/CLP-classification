"""
Modul pro klasifikaci ekotoxicity podle Přílohy I, část 4.1 nařízení CLP.
Implementuje klasifikaci na základě LC50, EC50 a NOEC hodnot z standardních testů.
"""

from typing import Optional, Tuple, Set


def assign_aquatic_acute_category(
    lc50_fish_96h: Optional[float],
    ec50_daphnia_48h: Optional[float],
    ec50_algae_72h: Optional[float]
) -> Optional[int]:
    """
    Přiřadí kategorii Aquatic Acute na základě standardních testů.
    
    Kritéria (Příloha I, tabulka 4.1.0):
    - Kategorie 1: LC50/EC50 ≤ 1 mg/L
    
    Použije nejnižší hodnotu ze všech dostupných testů (nejkonzervativnější přístup).
    
    Args:
        lc50_fish_96h: LC50 ryby, 96h v mg/L
        ec50_daphnia_48h: EC50 daphnie, 48h v mg/L
        ec50_algae_72h: EC50 řasy, 72h v mg/L
        
    Returns:
        1 pro Aquatic Acute 1, None pokud kritéria nesplněna
    """
    # Shromáždění všech dostupných hodnot
    available_values = []
    
    if lc50_fish_96h is not None and lc50_fish_96h > 0:
        available_values.append(lc50_fish_96h)
    
    if ec50_daphnia_48h is not None and ec50_daphnia_48h > 0:
        available_values.append(ec50_daphnia_48h)
    
    if ec50_algae_72h is not None and ec50_algae_72h > 0:
        available_values.append(ec50_algae_72h)
    
    # Pokud nejsou žádná data, nelze klasifikovat
    if not available_values:
        return None
    
    # Použij nejnižší hodnotu (nejpřísnější kritérium)
    min_value = min(available_values)
    
    # Kategorie 1: ≤ 1.0 mg/L
    if min_value <= 1.0:
        return 1
    
    return None


def assign_aquatic_chronic_category(
    lc50_fish_96h: Optional[float],
    ec50_daphnia_48h: Optional[float],
    ec50_algae_72h: Optional[float],
    noec_chronic: Optional[float],
    is_rapidly_degradable: bool = False,
    is_bioaccumulative: bool = False
) -> Optional[int]:
    """
    Přiřadí kategorii Aquatic Chronic na základě LC50/EC50 a NOEC.
    
    Kritéria (Příloha I, tabulka 4.1.0):
    - Kategorie 1: LC50/EC50 ≤ 1 mg/L A NENÍ rychle rozložitelná
                   NEBO NOEC < 0.1 mg/L A NENÍ rychle rozložitelná
    - Kategorie 2: 1 < LC50/EC50 ≤ 10 mg/L A NENÍ rychle rozložitelná
                   NEBO 0.1 ≤ NOEC ≤ 1 mg/L A NENÍ rychle rozložitelná
    - Kategorie 3: 10 < LC50/EC50 ≤ 100 mg/L A NENÍ rychle rozložitelná
                   NEBO 1 < NOEC ≤ 10 mg/L A NENÍ rychle rozložitelná
    - Kategorie 4: Dlouhodobé účinky (chybí data o rozložitelnosti)
    
    Args:
        lc50_fish_96h: LC50 ryby, 96h v mg/L
        ec50_daphnia_48h: EC50 daphnie, 48h v mg/L
        ec50_algae_72h: EC50 řasy, 72h v mg/L 
        noec_chronic: NOEC v mg/L
        is_rapidly_degradable: Je látka rychle rozložitelná?
        is_bioaccumulative: Je látka bioakumulativní?
        
    Returns:
        1-4 pro Aquatic Chronic 1-4, None pokud kritéria nesplněna
    """
    # Shromáždění akutních hodnot
    acute_values = []
    
    if lc50_fish_96h is not None and lc50_fish_96h > 0:
        acute_values.append(lc50_fish_96h)
    
    if ec50_daphnia_48h is not None and ec50_daphnia_48h > 0:
        acute_values.append(ec50_daphnia_48h)
    
    if ec50_algae_72h is not None and ec50_algae_72h > 0:
        acute_values.append(ec50_algae_72h)
    
    min_acute_value = min(acute_values) if acute_values else None
    
    # Klasifikace podle akutních hodnot (pokud NENÍ rychle rozložitelná)
    if min_acute_value is not None and not is_rapidly_degradable:
        if min_acute_value <= 1.0:
            return 1
        elif min_acute_value <= 10.0:
            return 2
        elif min_acute_value <= 100.0:
            return 3
    
    # Klasifikace podle NOEC
    if noec_chronic is not None:
        if is_rapidly_degradable:
            # Table 4.1.0(b)(iii)
            if noec_chronic <= 0.01:
                return 1
            elif noec_chronic <= 0.1:
                return 2
            elif noec_chronic <= 1.0:
                return 3
        else:
            # Table 4.1.0(b)(ii)
            if noec_chronic < 0.1:
                return 1
            elif noec_chronic <= 1.0:
                return 2
            elif noec_chronic <= 10.0:
                return 3
    
    # Kategorie 4: Dlouhodobé účinky
    # Pokud máme akutní data, ale nejsou kritéria pro 1-3, můžeme klasifikovat jako 4
    if min_acute_value is not None and min_acute_value > 100.0:
        # Látky, které nejsou rychle rozložitelné nebo jsou bioakumulativní
        if not is_rapidly_degradable or is_bioaccumulative:
            return 4
    
    return None


def get_h_code_from_ecotoxicity(
    acute_category: Optional[int],
    chronic_category: Optional[int]
) -> Tuple[Set[str], Set[str]]:
    """
    Převede kategorie ekotoxicity na H-kódy a GHS piktogramy.
    
    Args:
        acute_category: Aquatic Acute kategorie (1 nebo None)
        chronic_category: Aquatic Chronic kategorie (1-4 nebo None)
        
    Returns:
        (set of H-codes, set of GHS codes)
    """
    h_codes = set()
    ghs_codes = set()
    
    # Akutní toxicita
    if acute_category == 1:
        h_codes.add("H400")
        ghs_codes.add("GHS09")
    
    # Chronická toxicita
    if chronic_category == 1:
        h_codes.add("H410")
        ghs_codes.add("GHS09")
    elif chronic_category == 2:
        h_codes.add("H411")
        ghs_codes.add("GHS09")
    elif chronic_category == 3:
        h_codes.add("H412")
        # H412 nemá GHS09 piktogram
    elif chronic_category == 4:
        h_codes.add("H413")
        # H413 nemá piktogram
    
    return h_codes, ghs_codes


def classify_substance_ecotoxicity(
    lc50_fish_96h: Optional[float] = None,
    ec50_daphnia_48h: Optional[float] = None,
    ec50_algae_72h: Optional[float] = None,
    noec_chronic: Optional[float] = None,
    is_rapidly_degradable: bool = False,
    is_bioaccumulative: bool = False
) -> dict:
    """
    Úplná klasifikace ekotoxicity látky.
    
    Args:
        lc50_fish_96h: LC50 ryby, 96h v mg/L
        ec50_daphnia_48h: EC50 daphnie, 48h v mg/L
        ec50_algae_72h: EC50 řasy, 72h v mg/L
        noec_chronic: NOEC v mg/L
        is_rapidly_degradable: Je látka rychle rozložitelná?
        is_bioaccumulative: Je látka bioakumulativní?
        
    Returns:
        Slovník s výsledky klasifikace:
        {
            "acute_category": int nebo None,
            "chronic_category": int nebo None,
            "h_codes": set of str,
            "ghs_codes": set of str,
            "classification_basis": str (popis na čem je klasifikace založena)
        }
    """
    # Určení kategorií
    acute_cat = assign_aquatic_acute_category(
        lc50_fish_96h,
        ec50_daphnia_48h,
        ec50_algae_72h
    )
    
    chronic_cat = assign_aquatic_chronic_category(
        lc50_fish_96h,
        ec50_daphnia_48h,
        ec50_algae_72h,
        noec_chronic,
        is_rapidly_degradable,
        is_bioaccumulative
    )
    
    # Získání H-kódů a GHS
    h_codes, ghs_codes = get_h_code_from_ecotoxicity(acute_cat, chronic_cat)
    
    # Popis základu klasifikace
    basis_parts = []
    
    if lc50_fish_96h is not None:
        basis_parts.append(f"LC50(ryby,96h)={lc50_fish_96h} mg/L")
    
    if ec50_daphnia_48h is not None:
        basis_parts.append(f"EC50(daphnie,48h)={ec50_daphnia_48h} mg/L")
    
    if ec50_algae_72h is not None:
        basis_parts.append(f"EC50(řasy,72h)={ec50_algae_72h} mg/L")
    
    if noec_chronic is not None:
        basis_parts.append(f"NOEC={noec_chronic} mg/L")
    
    classification_basis = ", ".join(basis_parts) if basis_parts else "Žádná ekotoxická data"
    
    return {
        "acute_category": acute_cat,
        "chronic_category": chronic_cat,
        "h_codes": h_codes,
        "ghs_codes": ghs_codes,
        "classification_basis": classification_basis
    }
