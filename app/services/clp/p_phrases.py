"""
Služba pro přiřazování P-vět (Pokyny pro bezpečné zacházení) k výsledné klasifikaci.
"""
from typing import List, Set
from app.constants.p_phrases import H_TO_P_MAP, ALL_P_PHRASES, P_COMBINATIONS

from app.constants.clp import UserType

# P-věty relevantní pouze pro spotřebitele
CONSUMER_ONLY_PHRASES = {"P101", "P102"}

# P-věty relevantní pouze pro profesionály/průmysl (pokud existují specifické, zatím prázdné)
# PROFESSIONAL_ONLY_PHRASES = {}

# Priorita P-vět pro redukci (vyšší číslo = vyšší priorita)
# 1. Urgentní lékařská pomoc a reakce
# 2. Uchovávání mimo dosah dětí (pro spotřebitele kritické)
# 3. Prevence (Ochranné pomůcky)
# 4. Skladování
# 5. Odstraňování (často povinné, ale v hierarchii "bezpečnosti" při nehodě nižší než první pomoc)
P_PHRASE_PRIORITY = {
    "P101": 90, # Lékařská pomoc - obal
    "P102": 100, # Děti - nejvyšší priorita pro spotřebitele
    "P310": 95, "P301+P310": 95, "P304+P340": 95, # Okamžitá pomoc
    "P305+P351+P338": 90, # Oči - vyplachování
    "P280": 80, "P260": 80, "P284": 80, # Ochranné pomůcky - vysoká prevence
    "P210": 75, "P220": 75, # Hořlavost
    "P405": 60, # Uzamčené
    "P501": 50, # Odstraňování - důležité, ale často se "vejde"
    "P264": 40, # Mytí rukou - základní hygiena
    "P103": 10, # Čtěte pokyny - obecné
}

def assign_p_phrases(h_phrases: Set[str], user_type: UserType = UserType.PROFESSIONAL) -> List[str]:
    """
    Přiřadí P-věty na základě sady H-vět, typu uživatele a aplikuje pravidla pro redukci.
    
    Args:
        h_phrases: Množina H-kódů.
        user_type: Typ uživatele (určuje zobrazení spotřebitelských vět).
        
    Returns:
        Seznam unikátních P-kódů (max 6, dle priority).
    """
    p_codes = set()
    
    # 1. Agregace všech relevantních P-vět
    for h_code in h_phrases:
        if h_code in H_TO_P_MAP:
            p_codes.update(H_TO_P_MAP[h_code])
            
    # 2. Filtrace podle typu uživatele
    if user_type != UserType.CONSUMER:
        p_codes = {p for p in p_codes if p not in CONSUMER_ONLY_PHRASES}
    
    # 3. Redukce počtu P-vět (Max 6)
    # Článek 28 CLP: Max 6 vět, pokud povaha nebezpečnosti nevyžaduje více.
    if len(p_codes) > 6:
        # Seřadíme podle priority (sestupně) a poté podle kódu (pro determinismus)
        # Default priority is 50 if not specified
        sorted_by_priority = sorted(
            list(p_codes),
            key=lambda p: (-P_PHRASE_PRIORITY.get(p, 50), p)
        )
        # Vybereme top 6
        p_codes = set(sorted_by_priority[:6])

    # 4. Seřazení pro výstup
    sorted_p_codes = sorted(list(p_codes))
    
    return sorted_p_codes

def format_p_phrases(p_codes: List[str]) -> List[dict]:
    """
    Naformátuje seznam P-kódů do struktury pro zobrazení (kód + text).
    
    Args:
        p_codes: Seznam kódů P-vět.
        
    Returns:
        Seznam slovníků [{'code': 'P102', 'text': '...'}, ...].
    """
    result = []
    for code in p_codes:
        text = ALL_P_PHRASES.get(code, "Text nenalezen")
        result.append({"code": code, "text": text})
    return result
