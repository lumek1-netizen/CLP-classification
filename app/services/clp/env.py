from typing import Dict, List, Tuple, Set
from app.models import Mixture


def classify_environmental_hazards(
    mixture: Mixture,
) -> Tuple[Set, Set, List[Dict[str, str]]]:
    """Provádí klasifikaci nebezpečnosti pro životní prostředí."""
    env_hazards = set()
    env_ghs = set()
    log_entries = []

    sum_acute_1 = 0.0
    sum_chronic_1 = 0.0
    contributors_acute_1 = []
    contributors_chronic_1 = []

    sum_chronic_2 = 0.0
    sum_chronic_3 = 0.0
    sum_chronic_4 = 0.0
    contributors_chronic_2 = []
    contributors_chronic_3 = []
    contributors_chronic_4 = []

    # Nové třídy 2026
    ozone_names = []
    ed_env_names = []
    pbt_pmt_codes = set()

    for component in mixture.components:
        substance = component.substance
        concentration = component.concentration
        sub_name = substance.name

        if substance.env_h_phrases:
            env_h_codes = [h.strip() for h in substance.env_h_phrases.split(",")]
            for h_code in env_h_codes:
                if h_code == "H400":
                    if concentration < 0.1:
                        continue
                    m_factor = substance.m_factor_acute or 1
                    sum_acute_1 += concentration * m_factor
                    contributors_acute_1.append(
                        f"{sub_name} ({concentration}% x M{m_factor})"
                    )
                elif h_code == "H410":
                    if concentration < 0.1:
                        continue
                    m_factor = substance.m_factor_chronic or 1
                    sum_chronic_1 += concentration * m_factor
                    contributors_chronic_1.append(
                        f"{sub_name} ({concentration}% x M{m_factor})"
                    )
                elif h_code == "H411":
                    if concentration < 1.0:
                        continue
                    sum_chronic_2 += concentration
                    contributors_chronic_2.append(f"{sub_name} ({concentration}%)")
                elif h_code == "H412":
                    if concentration < 1.0:
                        continue
                    sum_chronic_3 += concentration
                    contributors_chronic_3.append(f"{sub_name} ({concentration}%)")
                elif h_code == "H413":
                    if concentration < 1.0:
                        continue
                    sum_chronic_4 += concentration
                    contributors_chronic_4.append(f"{sub_name} ({concentration}%)")

        # 2026 Třídy: Ozone, ED ENV, PBT/PMT
        if substance.has_ozone and concentration >= 0.1:
            ozone_names.append(sub_name)
        
        if substance.ed_env_cat:
            limit = 0.1 if substance.ed_env_cat == 1 else 1.0
            if concentration >= limit:
                ed_env_names.append((sub_name, substance.ed_env_cat))
        
        if concentration >= 0.1:
            if substance.is_pbt or substance.is_vpvb: pbt_pmt_codes.add("EUH450")
            if substance.is_pmt or substance.is_vpvm: pbt_pmt_codes.add("EUH451")

    if sum_acute_1 >= 25:
        env_hazards.add("H400")
        env_ghs.add("GHS09")
        log_entries.append(
            {
                "step": "Aquatic Acute 1",
                "detail": f"Součet = {sum_acute_1} >= 25",
                "result": "H400",
            }
        )

    if sum_chronic_1 >= 25:
        env_hazards.add("H410")
        env_ghs.add("GHS09")
        log_entries.append(
            {
                "step": "Aquatic Chronic 1",
                "detail": f"Součet = {sum_chronic_1} >= 25",
                "result": "H410",
            }
        )

    val_c2 = (10 * sum_chronic_1) + sum_chronic_2
    if val_c2 >= 25:
        if "H410" not in env_hazards:
            env_hazards.add("H411")
            env_ghs.add("GHS09")
        log_entries.append(
            {
                "step": "Aquatic Chronic 2",
                "detail": f"Vážený součet = {val_c2} >= 25",
                "result": "H411",
            }
        )

    val_c3 = (100 * sum_chronic_1) + (10 * sum_chronic_2) + sum_chronic_3
    if val_c3 >= 25:
        if "H410" not in env_hazards and "H411" not in env_hazards:
            env_hazards.add("H412")
        log_entries.append(
            {
                "step": "Aquatic Chronic 3",
                "detail": f"Vážený součet = {val_c3} >= 25",
                "result": "H412",
            }
        )

    # Aquatic Chronic 4 (H413) - Sumační metoda
    sum_c4_total = sum_chronic_1 + sum_chronic_2 + sum_chronic_3 + sum_chronic_4
    if sum_c4_total >= 25:
        if not any(h in env_hazards for h in ["H410", "H411", "H412"]):
            env_hazards.add("H413")
            log_entries.append({
                "step": "Aquatic Chronic 4",
                "detail": f"Součet = {sum_c4_total} >= 25",
                "result": "H413"
            })

    # 2026 Results logic
    if ozone_names:
        env_hazards.add("H420")
        env_ghs.add("GHS07") # Pro Ozone 1 je GHS07
        log_entries.append({"step": "Ozone", "detail": f"Obsahuje: {', '.join(ozone_names)}", "result": "H420"})

    for name, cat in ed_env_names:
        code = "EUH440" if cat == 1 else "EUH441"
        env_hazards.add(code)
    
    for code in pbt_pmt_codes:
        env_hazards.add(code)

    return env_hazards, env_ghs, log_entries
