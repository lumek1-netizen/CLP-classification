from typing import Dict, List, Tuple, Set, Any
from app.models import Mixture
from app.constants.clp import (
    SCL_HAZARD_TO_H_CODE,
    SCL_HAZARD_TO_GHS_CODE,
    STANDARD_CONCENTRATION_LIMITS,
)
from app.constants.classification_thresholds import (
    SKIN_CORROSION_THRESHOLD_PERCENT,
    SKIN_CORROSION_WEIGHT_MULTIPLIER,
    SKIN_IRRITATION_THRESHOLD_PERCENT,
    EYE_DAMAGE_THRESHOLD_PERCENT,
    EYE_DAMAGE_WEIGHT_MULTIPLIER,
    EYE_IRRITATION_THRESHOLD_PERCENT,
    STOT_SE3_THRESHOLD_PERCENT,
    ASPIRATION_HAZARD_THRESHOLD_PERCENT,
    LACTATION_THRESHOLD_PERCENT,
    ED_HH_CATEGORY_1_THRESHOLD_PERCENT,
    ED_HH_CATEGORY_2_THRESHOLD_PERCENT,
    CMR_CUTOFF_PERCENT,
    SENSITISATION_CUTOFF_PERCENT,
    STOT_CATEGORY_1_CUTOFF_PERCENT,
    AQUATIC_ACUTE_1_CUTOFF_PERCENT,
    GENERAL_CUTOFF_PERCENT,
)
from .scl import parse_scls, evaluate_scl_condition

# --- Konstanty pro klasifikaci ---

HAZARD_GROUPS = {
    "Skin": [
        "Skin Corr. 1",
        "Skin Corr. 1A",
        "Skin Corr. 1B",
        "Skin Corr. 1C",
        "Skin Irrit. 2",
    ],
    "Eye": ["Eye Dam. 1", "Eye Irrit. 2"],
    "RespSens": ["Resp. Sens. 1", "Resp. Sens. 1A", "Resp. Sens. 1B"],
    "SkinSens": ["Skin Sens. 1", "Skin Sens. 1A", "Skin Sens. 1B"],
    "Muta": ["Muta. 1A", "Muta. 1B", "Muta. 2"],
    "Carc": ["Carc. 1A", "Carc. 1B", "Carc. 2"],
    "Repr": ["Repr. 1A", "Repr. 1B", "Repr. 2"],
    "STOT_SE": ["STOT SE 1", "STOT SE 2", "STOT SE 3", "STOT SE 3 (Narcotic)"],
    "STOT_RE": ["STOT RE 1", "STOT RE 2"],
    "Lact": ["Lact."],
    "ED_HH": ["ED HH 1", "ED HH 2"],
    "Aquatic": [
        "Aquatic Acute 1",
        "Aquatic Chronic 1",
        "Aquatic Chronic 2",
        "Aquatic Chronic 3",
        "Aquatic Chronic 4",
    ],
    "AcuteTox": ["Acute Tox. 1", "Acute Tox. 2", "Acute Tox. 3", "Acute Tox. 4"],
    "AcuteToxDermal": [
        "Acute Tox. 1 (Dermal)",
        "Acute Tox. 2 (Dermal)",
        "Acute Tox. 3 (Dermal)",
        "Acute Tox. 4 (Dermal)",
    ],
    "AcuteToxOral": [
        "Acute Tox. 1 (Oral)",
        "Acute Tox. 2 (Oral)",
        "Acute Tox. 3 (Oral)",
        "Acute Tox. 4 (Oral)",
    ],
    "AcuteToxInhalation": [
        "Acute Tox. 1 (Inhalation)",
        "Acute Tox. 2 (Inhalation)",
        "Acute Tox. 3 (Inhalation)",
        "Acute Tox. 4 (Inhalation)",
    ],
}

CAT_TO_GROUP = {c: grp for grp, cats in HAZARD_GROUPS.items() for c in cats}

# Mapování H-vět na hazard groups
H_CODE_TO_GROUPS = {}
for cat, h_code in SCL_HAZARD_TO_H_CODE.items():
    if cat in CAT_TO_GROUP:
        grp = CAT_TO_GROUP[cat]
        if h_code not in H_CODE_TO_GROUPS:
            H_CODE_TO_GROUPS[h_code] = set()
        H_CODE_TO_GROUPS[h_code].add(grp)


def _get_cutoff_limit(hazard_category: str, h_code: str = None) -> float:
    """Vrátí mezní hodnotu (cut-off) pro uvažování látky v klasifikaci."""
    if any(x in hazard_category for x in ["Muta.", "Carc.", "Repr."]):
        return CMR_CUTOFF_PERCENT
    if "Sens." in hazard_category:
        return SENSITISATION_CUTOFF_PERCENT
    if any(x in hazard_category for x in ["STOT SE 1", "STOT RE 1"]):
        return STOT_CATEGORY_1_CUTOFF_PERCENT
    if any(x in hazard_category for x in ["Aquatic Acute 1", "Aquatic Chronic 1"]):
        return AQUATIC_ACUTE_1_CUTOFF_PERCENT
    if "ED HH" in hazard_category or "ED ENV" in hazard_category:
        return CMR_CUTOFF_PERCENT
    if "PBT" in hazard_category or "vPvB" in hazard_category or "PMT" in hazard_category or "vPvM" in hazard_category:
        return GENERAL_CUTOFF_PERCENT
    return GENERAL_CUTOFF_PERCENT


def _calculate_hazard_totals(mixture: Mixture) -> Dict[str, Dict[str, Any]]:
    """Vypočítá součty koncentrací pro jednotlivé kategorie hazardů."""
    hazard_totals = {}

    def add_contribution(category, concentration, sub_name, note="", forced_by_scl=False):
        if category not in hazard_totals:
            hazard_totals[category] = {"total": 0.0, "contributors": [], "forced_by_scl": False}
        hazard_totals[category]["total"] += concentration
        if forced_by_scl:
            hazard_totals[category]["forced_by_scl"] = True
        hazard_totals[category]["contributors"].append(
            f"{sub_name} ({concentration}%{note})"
        )

    for component in mixture.components:
        substance = component.substance
        conc = component.concentration
        sub_name = substance.name

        scl_covered_groups = set()
        parsed_scls_data = {}
        if substance.scl_limits:
            parsed_scls_data = parse_scls(substance.scl_limits)
            for scl_cat in parsed_scls_data.keys():
                clean_cat = scl_cat.split(";")[0].strip()
                if clean_cat in CAT_TO_GROUP:
                    scl_covered_groups.add(CAT_TO_GROUP[clean_cat])

        # 1. SCL Vyhodnocení
        for scl_cat, conditions in parsed_scls_data.items():
            if evaluate_scl_condition(conc, conditions):
                clean_cat = scl_cat.split(";")[0].strip()
                target_cat = clean_cat
                if target_cat.startswith("Skin Corr. 1"):
                    target_cat = "Skin Corr. 1"
                cond_str = ", ".join([f"{c['op']}{c['value']}" for c in conditions])
                add_contribution(target_cat, conc, sub_name, f" [SCL {cond_str}]", forced_by_scl=True)

        # 2. GCL / Standardní limity z H-vět
        if substance.health_h_phrases:
            h_codes = [h.strip() for h in substance.health_h_phrases.split(",")]
            processed_groups = set()
            for h_code in h_codes:
                possible_groups = H_CODE_TO_GROUPS.get(h_code, set())
                for group in possible_groups:
                    if group in scl_covered_groups or group in processed_groups:
                        continue

                    target_cat = _get_target_category_from_hcode(h_code, group)

                    if target_cat:
                        limit_info = STANDARD_CONCENTRATION_LIMITS.get(target_cat, {})
                        gcl = limit_info.get("cl", 100.0)
                        cutoff = _get_cutoff_limit(target_cat, h_code)
                        if conc < cutoff:
                            continue

                        is_additive = group in ["Skin", "Eye", "Aquatic"] or h_code in [
                            "H335",
                            "H336",
                        ]
                        if is_additive:
                            sum_cat = target_cat
                            if target_cat in ["STOT SE 3", "STOT SE 3 (Narcotic)"]:
                                sum_cat = "STOT SE 3"
                            add_contribution(sum_cat, conc, sub_name, f" [{h_code}]")
                        elif conc >= gcl:
                            add_contribution(
                                target_cat, conc, sub_name, f" (>= GCL {gcl}%)"
                            )

                    processed_groups.add(group)

        # 3. Aspirační toxicita (speciální pravidlo)
        if substance.health_h_phrases and "H304" in substance.health_h_phrases:
            if conc >= ASPIRATION_HAZARD_THRESHOLD_PERCENT:
                add_contribution("Asp. Tox. 1", conc, sub_name, f" (>= {ASPIRATION_HAZARD_THRESHOLD_PERCENT}%)")

        # 4. Speciální třídy 2026 (Lact, ED HH)
        if substance.is_lact and conc >= LACTATION_THRESHOLD_PERCENT:
            add_contribution("Lact.", conc, sub_name, f" (>= {LACTATION_THRESHOLD_PERCENT}%)")
        
        if substance.ed_hh_cat:
            cat_name = f"ED HH {substance.ed_hh_cat}"
            limit = ED_HH_CATEGORY_1_THRESHOLD_PERCENT if substance.ed_hh_cat == 1 else ED_HH_CATEGORY_2_THRESHOLD_PERCENT
            if conc >= limit:
                add_contribution(cat_name, conc, sub_name, f" (>= {limit}%)")

    return hazard_totals


def _get_target_category_from_hcode(h_code: str, group: str) -> str:
    """Vrátí cílovou kategorii hazardu pro danou H-větu a skupinu."""
    if group == "Skin":
        if h_code == "H314":
            return "Skin Corr. 1"
        if h_code == "H315":
            return "Skin Irrit. 2"
    elif group == "Eye":
        if h_code == "H318":
            return "Eye Dam. 1"
        if h_code == "H319":
            return "Eye Irrit. 2"
    elif group == "STOT_SE" and h_code == "H336":
        return "STOT SE 3 (Narcotic)"
    
    # Akutní toxicita - Dermální
    elif group == "AcuteToxDermal":
        if h_code == "H310":
            return "Acute Tox. 1 (Dermal)"  # Kat. 1 a 2 mají stejnou H-větu
        if h_code == "H311":
            return "Acute Tox. 3 (Dermal)"
        if h_code == "H312":
            return "Acute Tox. 4 (Dermal)"
    
    # Akutní toxicita - Orální
    elif group == "AcuteToxOral":
        if h_code == "H300":
            return "Acute Tox. 1 (Oral)"  # Kat. 1 a 2 mají stejnou H-větu
        if h_code == "H301":
            return "Acute Tox. 3 (Oral)"
        if h_code == "H302":
            return "Acute Tox. 4 (Oral)"
    
    # Akutní toxicita - Inhalační
    elif group == "AcuteToxInhalation":
        if h_code == "H330":
            return "Acute Tox. 1 (Inhalation)"  # Kat. 1 a 2 mají stejnou H-větu
        if h_code == "H331":
            return "Acute Tox. 3 (Inhalation)"
        if h_code == "H332":
            return "Acute Tox. 4 (Inhalation)"

    # Generic lookup
    for cat_name, h in SCL_HAZARD_TO_H_CODE.items():
        if h == h_code and CAT_TO_GROUP.get(cat_name) == group:
            return cat_name
    return None


def _evaluate_skin_eye_hazards(hazard_totals, health_hazards, health_ghs, log_entries):
    """Vyhodnotí poleptání a podráždění kůže a očí."""
    # Skin
    sum_skin_1 = hazard_totals.get("Skin Corr. 1", {}).get("total", 0.0)
    sum_skin_2 = hazard_totals.get("Skin Irrit. 2", {}).get("total", 0.0)

    if sum_skin_1 >= SKIN_CORROSION_THRESHOLD_PERCENT or hazard_totals.get("Skin Corr. 1", {}).get("forced_by_scl"):
        health_hazards.add("H314")
        health_ghs.add("GHS05")
        detail = f"Součet = {sum_skin_1}% >= {SKIN_CORROSION_THRESHOLD_PERCENT}%"
        if hazard_totals.get("Skin Corr. 1", {}).get("forced_by_scl"):
            detail = f"Vynuceno přes SCL (Součet = {sum_skin_1}%)"
            
        log_entries.append(
            {
                "step": "Skin Corr. 1",
                "detail": detail,
                "result": "H314",
            }
        )
    else:
        val_skin_2 = (SKIN_CORROSION_WEIGHT_MULTIPLIER * sum_skin_1) + sum_skin_2
        if val_skin_2 >= SKIN_IRRITATION_THRESHOLD_PERCENT or hazard_totals.get("Skin Irrit. 2", {}).get("forced_by_scl"):
            health_hazards.add("H315")
            health_ghs.add("GHS07")
            detail = f"Vážený součet = {val_skin_2}% >= {SKIN_IRRITATION_THRESHOLD_PERCENT}%"
            if hazard_totals.get("Skin Irrit. 2", {}).get("forced_by_scl"):
                detail = f"Vynuceno přes SCL (Vážený součet = {val_skin_2}%)"
            log_entries.append(
                {
                    "step": "Skin Irrit. 2",
                    "detail": detail,
                    "result": "H315",
                }
            )

    # Eye
    sum_eye_1 = hazard_totals.get("Eye Dam. 1", {}).get("total", 0.0) + sum_skin_1
    sum_eye_2 = hazard_totals.get("Eye Irrit. 2", {}).get("total", 0.0)

    if sum_eye_1 >= EYE_DAMAGE_THRESHOLD_PERCENT or hazard_totals.get("Eye Dam. 1", {}).get("forced_by_scl"):
        health_hazards.add("H318")
        health_ghs.add("GHS05")
        detail = f"Součet = {sum_eye_1}% >= {EYE_DAMAGE_THRESHOLD_PERCENT}%"
        if hazard_totals.get("Eye Dam. 1", {}).get("forced_by_scl"):
            detail = f"Vynuceno přes SCL (Součet = {sum_eye_1}%)"
        log_entries.append(
            {
                "step": "Eye Dam. 1",
                "detail": detail,
                "result": "H318",
            }
        )
    else:
        val_eye_2 = (EYE_DAMAGE_WEIGHT_MULTIPLIER * sum_eye_1) + sum_eye_2
        if val_eye_2 >= EYE_IRRITATION_THRESHOLD_PERCENT or hazard_totals.get("Eye Irrit. 2", {}).get("forced_by_scl"):
            health_hazards.add("H319")
            health_ghs.add("GHS07")
            detail = f"Vážený součet = {val_eye_2}% >= {EYE_IRRITATION_THRESHOLD_PERCENT}%"
            if hazard_totals.get("Eye Irrit. 2", {}).get("forced_by_scl"):
                detail = f"Vynuceno přes SCL (Vážený součet = {val_eye_2}%)"
            log_entries.append(
                {
                    "step": "Eye Irrit. 2",
                    "detail": detail,
                    "result": "H319",
                }
            )


def _evaluate_acute_toxicity_hazards(hazard_totals, health_hazards, health_ghs, log_entries):
    """Vyhodnotí akutní toxicitu (Acute Tox 3/4) pro všechny cesty expozice."""
    
    # Definice kategorií a jejich priorit (1 > 2 > 3 > 4)
    # Zpracováváme pouze kategorie 3 a 4, protože 1 a 2 se řeší přes ATEmix
    categories = [
        ("Acute Tox. 3 (Dermal)", "H311", "GHS06"),
        ("Acute Tox. 4 (Dermal)", "H312", "GHS07"),
        ("Acute Tox. 3 (Oral)", "H301", "GHS06"),
        ("Acute Tox. 4 (Oral)", "H302", "GHS07"),
        ("Acute Tox. 3 (Inhalation)", "H331", "GHS06"),
        ("Acute Tox. 4 (Inhalation)", "H332", "GHS07"),
    ]
    
    for cat, h_code, ghs_code in categories:
        if cat in hazard_totals and hazard_totals[cat]["total"] > 0:
            health_hazards.add(h_code)
            health_ghs.add(ghs_code)
            contributors = hazard_totals[cat]["contributors"]
            log_entries.append({
                "step": cat,
                "detail": f"Splněno: {', '.join(contributors)}",
                "result": h_code,
            })


def _evaluate_stot_se3(hazard_totals, health_hazards, health_ghs, log_entries):
    """Vyhodnotí STOT SE 3 (podráždění dýchacích cest a narkotické účinky)."""
    sum_stot_se3 = hazard_totals.get("STOT SE 3", {}).get("total", 0.0)
    stot_se3_contribs = hazard_totals.get("STOT SE 3", {}).get("contributors", [])
    forced_by_scl = hazard_totals.get("STOT SE 3", {}).get("forced_by_scl", False)
    
    if sum_stot_se3 >= STOT_SE3_THRESHOLD_PERCENT or forced_by_scl:
        # Detekce H335 vs H336 z contributors
        has_h335 = any("H335" in c or "STOT SE 3" in c for c in stot_se3_contribs)
        has_h336 = any("H336" in c or "Narcotic" in c for c in stot_se3_contribs)
        
        # Pro SCL případy: pokud není explicitně H336, předpokládáme H335
        # (STOT SE 3 standardně znamená H335, H336 je speciální případ pro narkotické účinky)
        if forced_by_scl and not has_h335 and not has_h336:
            has_h335 = True
        
        if has_h335:
            health_hazards.add("H335")
        if has_h336:
            health_hazards.add("H336")
        if has_h335 or has_h336:
            health_ghs.add("GHS07")
            detail = f"Součet = {sum_stot_se3}% >= {STOT_SE3_THRESHOLD_PERCENT}%"
            if forced_by_scl:
                detail = f"Vynuceno přes SCL (Součet = {sum_stot_se3}%)"
            log_entries.append(
                {
                    "step": "STOT SE 3",
                    "detail": detail,
                    "result": "H335/H336",
                }
            )


def _evaluate_generic_hazards(hazard_totals, health_hazards, health_ghs, log_entries):
    """Vyhodnotí ostatní hazardy (CMR, STOT, Sens) bez aditivity."""
    ignored_cats = [
        "Skin Corr. 1",
        "Skin Irrit. 2",
        "Eye Dam. 1",
        "Eye Irrit. 2",
        "STOT SE 3",
        "Asp. Tox. 1",
        "Lact.",
        "ED HH 1",
        "ED HH 2",
        # Akutní toxicita (zpracováno v _evaluate_acute_toxicity_hazards)
        "Acute Tox. 1 (Dermal)",
        "Acute Tox. 2 (Dermal)",
        "Acute Tox. 3 (Dermal)",
        "Acute Tox. 4 (Dermal)",
        "Acute Tox. 1 (Oral)",
        "Acute Tox. 2 (Oral)",
        "Acute Tox. 3 (Oral)",
        "Acute Tox. 4 (Oral)",
        "Acute Tox. 1 (Inhalation)",
        "Acute Tox. 2 (Inhalation)",
        "Acute Tox. 3 (Inhalation)",
        "Acute Tox. 4 (Inhalation)",
    ]
    for cat, data in hazard_totals.items():
        if cat in ignored_cats or cat.startswith("Aquatic"):
            continue
        if data["total"] > 0:
            h_code = SCL_HAZARD_TO_H_CODE.get(cat)
            ghs_code = SCL_HAZARD_TO_GHS_CODE.get(cat)
            if h_code:
                health_hazards.add(h_code)
            if ghs_code:
                health_ghs.add(ghs_code)
            log_entries.append(
                {
                    "step": cat,
                    "detail": f"Splněno: {', '.join(data['contributors'])}",
                    "result": f"H_CODE: {h_code}",
                }
            )


def classify_by_concentration_limits(
    mixture: Mixture,
) -> Tuple[Set, Set, List[Dict[str, str]]]:
    """Provádí klasifikaci směsi na základě součtu koncentrací látek (Health hazards)."""
    try:
        health_hazards = set()
        health_ghs = set()
        log_entries = []

        hazard_totals = _calculate_hazard_totals(mixture)

        # 1. Skin & Eye
        _evaluate_skin_eye_hazards(
            hazard_totals, health_hazards, health_ghs, log_entries
        )

        # 2. STOT SE 3
        _evaluate_stot_se3(hazard_totals, health_hazards, health_ghs, log_entries)

        # 3. Asp. Tox. 1
        if hazard_totals.get("Asp. Tox. 1", {}).get("total", 0.0) >= ASPIRATION_HAZARD_THRESHOLD_PERCENT:
            health_hazards.add("H304")
            log_entries.append(
                {"step": "Asp. Tox. 1", "detail": f"Součet >= {ASPIRATION_HAZARD_THRESHOLD_PERCENT}%", "result": "H304"}
            )

        # 4. Acute Toxicity (NEW)
        _evaluate_acute_toxicity_hazards(
            hazard_totals, health_hazards, health_ghs, log_entries
        )

        # 5. Generic (Sens, CMR, STOT RE/SE 1/2)
        _evaluate_generic_hazards(
            hazard_totals, health_hazards, health_ghs, log_entries
        )

        # 5. Lactation & ED (Newer requirements)
        if hazard_totals.get("Lact.", {}).get("total", 0.0) > 0:
            health_hazards.add("H362")
            log_entries.append({"step": "Lactation", "detail": f"Splněno (>= {LACTATION_THRESHOLD_PERCENT}%)", "result": "H362"})
        
        if hazard_totals.get("ED HH 1", {}).get("total", 0.0) > 0:
            health_hazards.add("EUH430")
        if hazard_totals.get("ED HH 2", {}).get("total", 0.0) > 0:
            health_hazards.add("EUH431")

        return health_hazards, health_ghs, log_entries

    except Exception as e:
        return (
            set(),
            set(),
            [{"step": "CHYBA", "detail": str(e), "result": "Selhání klasifikace"}],
        )
