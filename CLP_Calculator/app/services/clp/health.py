from typing import Dict, List, Tuple, Set
from app.models import Mixture
from app.constants.clp import (
    SCL_HAZARD_TO_H_CODE, SCL_HAZARD_TO_GHS_CODE, 
    STANDARD_CONCENTRATION_LIMITS
)
from .scl import parse_scls, evaluate_scl_condition

def _get_cutoff_limit(hazard_category: str, h_code: str = None) -> float:
    """Vrátí mezní hodnotu (cut-off) pro uvažování látky v klasifikaci."""
    if any(x in hazard_category for x in ['Muta.', 'Carc.', 'Repr.']): return 0.1
    if 'Sens.' in hazard_category: return 0.1
    if any(x in hazard_category for x in ['STOT SE 1', 'STOT RE 1']): return 0.1
    if any(x in hazard_category for x in ['Aquatic Acute 1', 'Aquatic Chronic 1']): return 0.1
    return 1.0

def classify_by_concentration_limits(mixture: Mixture) -> Tuple[Set, Set, List[Dict[str, str]]]:
    """Provádí klasifikaci směsi na základě součtu koncentrací látek (Health hazards)."""
    health_hazards = set()
    health_ghs = set()
    log_entries = []
    hazard_totals = {}

    def add_contribution(category, concentration, sub_name, note=""):
        if category not in hazard_totals:
            hazard_totals[category] = {'total': 0.0, 'contributors': []}
        hazard_totals[category]['total'] += concentration
        hazard_totals[category]['contributors'].append(f"{sub_name} ({concentration}%{note})")

    HAZARD_GROUPS = {
        'Skin': ['Skin Corr. 1', 'Skin Corr. 1A', 'Skin Corr. 1B', 'Skin Corr. 1C', 'Skin Irrit. 2'],
        'Eye': ['Eye Dam. 1', 'Eye Irrit. 2'],
        'RespSens': ['Resp. Sens. 1', 'Resp. Sens. 1A', 'Resp. Sens. 1B'],
        'SkinSens': ['Skin Sens. 1', 'Skin Sens. 1A', 'Skin Sens. 1B'],
        'Muta': ['Muta. 1A', 'Muta. 1B', 'Muta. 2'],
        'Carc': ['Carc. 1A', 'Carc. 1B', 'Carc. 2'],
        'Repr': ['Repr. 1A', 'Repr. 1B', 'Repr. 2'],
        'STOT_SE': ['STOT SE 1', 'STOT SE 2', 'STOT SE 3', 'STOT SE 3 (Narcotic)'], 
        'STOT_RE': ['STOT RE 1', 'STOT RE 2'],
        'Aquatic': ['Aquatic Acute 1', 'Aquatic Chronic 1', 'Aquatic Chronic 2', 'Aquatic Chronic 3', 'Aquatic Chronic 4']
    }
    
    CAT_TO_GROUP = {c: grp for grp, cats in HAZARD_GROUPS.items() for c in cats}
    H_CODE_TO_GROUPS = {}
    for cat, h_code in SCL_HAZARD_TO_H_CODE.items():
        if cat in CAT_TO_GROUP:
            grp = CAT_TO_GROUP[cat]
            if h_code not in H_CODE_TO_GROUPS: H_CODE_TO_GROUPS[h_code] = set()
            H_CODE_TO_GROUPS[h_code].add(grp)

    for component in mixture.components:
        substance = component.substance
        conc = component.concentration
        sub_name = substance.name
        
        scl_covered_groups = set()
        parsed_scls_data = {}
        if substance.scl_limits:
            parsed_scls_data = parse_scls(substance.scl_limits)
            for scl_cat in parsed_scls_data.keys():
                clean_cat = scl_cat.split(';')[0].strip()
                if clean_cat in CAT_TO_GROUP:
                    scl_covered_groups.add(CAT_TO_GROUP[clean_cat])
        
        for scl_cat, conditions in parsed_scls_data.items():
            if evaluate_scl_condition(conc, conditions):
                clean_cat = scl_cat.split(';')[0].strip()
                target_cat = clean_cat
                if target_cat.startswith('Skin Corr. 1'): target_cat = 'Skin Corr. 1'
                cond_str = ", ".join([f"{c['op']}{c['value']}" for c in conditions])
                add_contribution(target_cat, conc, sub_name, f" [SCL {cond_str}]")
        
        if substance.health_h_phrases:
            h_codes = [h.strip() for h in substance.health_h_phrases.split(',')]
            processed_groups = set()
            for h_code in h_codes:
                possible_groups = H_CODE_TO_GROUPS.get(h_code, set())
                for group in possible_groups:
                    if group in scl_covered_groups or group in processed_groups: continue
                    
                    target_cat = None
                    if group == 'Skin':
                        if h_code == 'H314': target_cat = 'Skin Corr. 1'
                        elif h_code == 'H315': target_cat = 'Skin Irrit. 2'
                    elif group == 'Eye':
                        if h_code == 'H318': target_cat = 'Eye Dam. 1'
                        elif h_code == 'H319': target_cat = 'Eye Irrit. 2'
                    elif group == 'Aquatic':
                        # Should be handled in env.py, but we keep the logic for consistent summation if needed
                        pass 
                    elif group == 'STOT_SE' and h_code == 'H336':
                        target_cat = 'STOT SE 3 (Narcotic)'
                    else:
                        for cat_name, h in SCL_HAZARD_TO_H_CODE.items():
                            if h == h_code and CAT_TO_GROUP.get(cat_name) == group:
                                target_cat = cat_name
                                break
                    
                    if target_cat:
                        limit_info = STANDARD_CONCENTRATION_LIMITS.get(target_cat, {})
                        gcl = limit_info.get('cl', 100.0)
                        cutoff = _get_cutoff_limit(target_cat, h_code)
                        if conc < cutoff: continue

                        is_additive = group in ['Skin', 'Eye', 'Aquatic'] or h_code in ['H335', 'H336']
                        if is_additive:
                            sum_cat = target_cat
                            if target_cat in ['STOT SE 3', 'STOT SE 3 (Narcotic)']: sum_cat = 'STOT SE 3'
                            add_contribution(sum_cat, conc, sub_name, f" [{h_code}]")
                        elif conc >= gcl:
                            add_contribution(target_cat, conc, sub_name, f" (>= GCL {gcl}%)")
                    
                    processed_groups.add(group)

        if substance.health_h_phrases and 'H304' in substance.health_h_phrases:
            if conc >= 10.0: add_contribution('Asp. Tox. 1', conc, sub_name, " (>= 10%)")

    # Evaluation
    sum_skin_1 = hazard_totals.get('Skin Corr. 1', {}).get('total', 0.0)
    sum_skin_2 = hazard_totals.get('Skin Irrit. 2', {}).get('total', 0.0)
    skin_1_contribs = hazard_totals.get('Skin Corr. 1', {}).get('contributors', [])
    skin_2_contribs = hazard_totals.get('Skin Irrit. 2', {}).get('contributors', [])

    if sum_skin_1 >= 5.0:
        health_hazards.add('H314')
        health_ghs.add('GHS05')
        log_entries.append({"step": "Skin Corr. 1", "detail": f"Součet = {sum_skin_1}% >= 5%", "result": "H314"})
    else:
        val_skin_2 = (10 * sum_skin_1) + sum_skin_2
        if val_skin_2 >= 10.0:
            health_hazards.add('H315')
            health_ghs.add('GHS07')
            log_entries.append({"step": "Skin Irrit. 2", "detail": f"Vážený součet = {val_skin_2}% >= 10%", "result": "H315"})

    sum_eye_1 = hazard_totals.get('Eye Dam. 1', {}).get('total', 0.0) + sum_skin_1
    sum_eye_2 = hazard_totals.get('Eye Irrit. 2', {}).get('total', 0.0)
    eye_1_contribs = hazard_totals.get('Eye Dam. 1', {}).get('contributors', []) + skin_1_contribs

    if sum_eye_1 >= 3.0:
        health_hazards.add('H318')
        health_ghs.add('GHS05')
        log_entries.append({"step": "Eye Dam. 1", "detail": f"Součet = {sum_eye_1}% >= 3%", "result": "H318"})
    else:
        val_eye_2 = (10 * sum_eye_1) + sum_eye_2
        if val_eye_2 >= 10.0:
            health_hazards.add('H319')
            health_ghs.add('GHS07')
            log_entries.append({"step": "Eye Irrit. 2", "detail": f"Vážený součet = {val_eye_2}% >= 10%", "result": "H319"})

    sum_stot_se3 = hazard_totals.get('STOT SE 3', {}).get('total', 0.0)
    stot_se3_contribs = hazard_totals.get('STOT SE 3', {}).get('contributors', [])
    if sum_stot_se3 >= 20.0:
        has_h335 = any('H335' in c or 'STOT SE 3' in c for c in stot_se3_contribs)
        has_h336 = any('H336' in c or 'STOT SE 3' in c for c in stot_se3_contribs)
        if has_h335: health_hazards.add('H335')
        if has_h336: health_hazards.add('H336')
        if has_h335 or has_h336:
            health_ghs.add('GHS07')
            log_entries.append({"step": "STOT SE 3", "detail": f"Součet = {sum_stot_se3}% >= 20%", "result": "Klasifikováno"})

    if hazard_totals.get('Asp. Tox. 1', {}).get('total', 0.0) >= 10.0:
        health_hazards.add('H304')
        log_entries.append({"step": "Asp. Tox. 1", "detail": "Součet >= 10%", "result": "H304"})

    ignored_cats = ['Skin Corr. 1', 'Skin Irrit. 2', 'Eye Dam. 1', 'Eye Irrit. 2', 'STOT SE 3', 'Asp. Tox. 1']
    for cat, data in hazard_totals.items():
        if cat in ignored_cats or cat.startswith('Aquatic'): continue
        if data['total'] > 0:
            h_code = SCL_HAZARD_TO_H_CODE.get(cat)
            ghs_code = SCL_HAZARD_TO_GHS_CODE.get(cat)
            if h_code: health_hazards.add(h_code)
            if ghs_code: health_ghs.add(ghs_code)
            log_entries.append({"step": cat, "detail": f"Splněno: {', '.join(data['contributors'])}", "result": f"H_CODE: {h_code}"})

    return health_hazards, health_ghs, log_entries
