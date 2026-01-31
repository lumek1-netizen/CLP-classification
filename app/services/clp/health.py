"""
Modul pro klasifikaci nebezpečnosti pro zdraví.

Implementuje logiku pro klasifikaci zdravotních rizik (Health Hazards) podle nařízení CLP.
Zahrnuje vyhodnocení:
- Akutní toxicity (mimo ATEmix)
- Žíravosti/dráždivosti pro kůži a oči
- Senzibilizace, Mutagenity, Karcinogenity, Toxicity pro reprodukci (CMR)
- STOT SE a RE
- Nebezpečnosti při vdechnutí
- Endokrinní disrupce pro zdraví (ED HH)
"""

from typing import Dict, List, Tuple, Set, Any, Optional
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

# --- Konstanty pro klasifikaci (Strukturní metadata) ---

HAZARD_GROUPS = {
    "Skin": ["Skin Corr. 1", "Skin Corr. 1A", "Skin Corr. 1B", "Skin Corr. 1C", "Skin Irrit. 2"],
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
}

CAT_TO_GROUP = {c: grp for grp, cats in HAZARD_GROUPS.items() for c in cats}

# Mapování H-vět na hazard groups (předpočítané pro výkon)
H_CODE_TO_GROUPS = {}
for cat, h_code in SCL_HAZARD_TO_H_CODE.items():
    if cat in CAT_TO_GROUP:
        grp = CAT_TO_GROUP[cat]
        H_CODE_TO_GROUPS.setdefault(h_code, set()).add(grp)

# Doplnění specifických Repr variant
for h_code in ["H360F", "H360D", "H360FD", "H360Fd", "H360Df", "H361f", "H361d", "H361fd"]:
    H_CODE_TO_GROUPS.setdefault(h_code, set()).add("Repr")


class HealthHazardClassifier:
    """
    Kalkulátor pro klasifikaci nebezpečnosti směsi pro zdraví.
    Implementuje aditivní i neaditivní metody podle nařízení CLP.
    """

    def __init__(self, mixture: Mixture, components: Optional[List] = None):
        self.mixture = mixture
        self.components = components if components is not None else mixture.components
        self.hazard_totals: Dict[str, Dict[str, Any]] = {}
        self.health_hazards: Set[str] = set()
        self.health_ghs: Set[str] = set()
        self.log_entries: List[Dict[str, str]] = []

    def classify(self) -> Tuple[Set[str], Set[str], List[Dict[str, str]]]:
        """Hlavní metoda provádějící celý proces klasifikace."""
        try:
            self._evaluate_extreme_ph()
            self._calculate_all_hazard_totals()
            
            # Jednotlivé kroky evaluace (pořadí je důležité dle CLP)
            self._evaluate_skin_eye_hazards()
            self._evaluate_stot_se3()
            self._evaluate_aspiration_hazard()
            self._evaluate_acute_toxicity_hazards()
            self._evaluate_generic_hazards()
            self._evaluate_modern_hazards() # Lactation, ED

            return self.health_hazards, self.health_ghs, self.log_entries
        except Exception as e:
            return (
                set(),
                set(),
                [{"step": "CHYBA", "detail": str(e), "result": "Selhání klasifikace"}],
            )

    def _add_contribution(self, category: str, concentration: float, sub_name: str, 
                         note: str = "", forced_by_scl: bool = False) -> None:
        """Interní pomocník pro přičítání koncentrací do kategorií."""
        if category not in self.hazard_totals:
            self.hazard_totals[category] = {"total": 0.0, "contributors": [], "forced_by_scl": False}
        
        self.hazard_totals[category]["total"] += concentration
        if forced_by_scl:
            self.hazard_totals[category]["forced_by_scl"] = True
            
        self.hazard_totals[category]["contributors"].append(
            f"{sub_name} ({concentration:.3f}%{note})"
        )

    def _evaluate_extreme_ph(self) -> None:
        """Provede kontrolu extrémního pH podle CLP Přílohy I, bod 3.2.3.1.2."""
        if self.mixture.ph is not None:
            if self.mixture.ph <= 2 or self.mixture.ph >= 11.5:
                self.health_hazards.add("H314")
                self.health_ghs.add("GHS05")
                self.log_entries.append({
                    "step": "pH check",
                    "detail": f"Hodnota pH={self.mixture.ph} (extrémní kyselost/zásaditost)",
                    "result": "H314 (Skin Corr. 1)"
                })

    def _calculate_all_hazard_totals(self) -> None:
        """Projde všechny komponenty a vypočítá jejich příspěvky do kategorií."""
        for component in self.components:
            self._process_component_contribution(component)

    def _process_component_contribution(self, component) -> None:
        """Zpracuje jednu složku směsi."""
        substance = component.substance
        conc = component.concentration
        sub_name = substance.name

        # 1. Analýza SCL (Specifické koncentrační limity)
        parsed_scls = {}
        if substance.scl_limits:
            parsed_scls = parse_scls(substance.scl_limits)
            self._apply_scl_direct_hits(sub_name, conc, parsed_scls)

        # 2. Aditivní a GCL příspěvky na základě H-vět
        if substance.health_h_phrases:
            self._apply_h_phrase_contributions(sub_name, conc, substance.health_h_phrases, parsed_scls)

    def _apply_scl_direct_hits(self, name: str, conc: float, parsed_scls: dict) -> None:
        """Zpracuje SCL 'přímé zásahy' (pokud látka sama o sobě překročí svůj SCL)."""
        for scl_cat, conditions in parsed_scls.items():
            target_cat = scl_cat.split(";")[0].strip()
            if target_cat.startswith("Skin Corr. 1"):
                target_cat = "Skin Corr. 1"
            
            if evaluate_scl_condition(conc, conditions):
                cond_str = ", ".join([f"{c['op']}{c['value']}" for c in conditions])
                self._add_contribution(target_cat, conc, name, f" [SCL {cond_str} OK]", forced_by_scl=True)

    def _apply_h_phrase_contributions(self, name: str, conc: float, h_phrases_str: str, parsed_scls: dict) -> None:
        """Vypočítá příspěvky složky do sumačních kategorií na základě jejích H-vět."""
        h_codes = [h.strip() for h in h_phrases_str.split(",")]
        
        for h_code in h_codes:
            possible_groups = H_CODE_TO_GROUPS.get(h_code, set())
            for group in possible_groups:
                target_cat = self._get_target_category(h_code, group)
                if not target_cat:
                    continue

                # Získání relevantního SCL pro vážení
                scl_limit_val = self._find_relevant_scl(target_cat, parsed_scls)
                
                # Určení váhy (Standard GCL / SCL)
                weight = 1.0
                standard_limit = self._get_threshold(target_cat)
                note = f" [{h_code}]"

                if scl_limit_val and scl_limit_val > 0:
                    weight = standard_limit / scl_limit_val
                    if weight != 1.0:
                        note += f" (SCL {scl_limit_val}% -> x{weight:.2f})"

                # Cut-off kontrola
                cutoff = min(self._get_cutoff(target_cat, h_code), scl_limit_val or 100.0)
                if conc < cutoff:
                    continue

                # Přičtení (aditivní vs neaditivní)
                is_additive = group in ["Skin", "Eye", "Aquatic"] or h_code in ["H335", "H336"]
                if is_additive:
                    # PRO STOT SE 3 (H335 a H336) NEPOUŽÍVÁME "STOT SE 3" jako sumární klíč,
                    # ale zachováváme jejich specifické target_cat ("STOT SE 3" pro H335 a "STOT SE 3 (Narcotic)" pro H336)
                    # aby se nesčítaly dohromady.
                    sum_cat = target_cat 
                    if target_cat.startswith("STOT SE 3") and h_code == "H335":
                         sum_cat = "STOT SE 3" # Pro jistotu, H335 mapuje na STOT SE 3
                    elif target_cat.startswith("STOT SE 3") and h_code == "H336":
                         sum_cat = "STOT SE 3 (Narcotic)"

                    self._add_contribution(sum_cat, conc * weight, name, note)
                elif conc >= standard_limit and not scl_limit_val:
                    # Neaditivní bez SCL, překročilo standardní limit
                    self._add_contribution(target_cat, conc, name, f" (>= GCL {standard_limit}%)")

    def _find_relevant_scl(self, target_cat: str, parsed_scls: dict) -> Optional[float]:
        """Najde číselnou hodnotu limitu v parsed SCL datech."""
        keys = [k for k in parsed_scls.keys() if k.startswith(target_cat.replace(" Corr. 1", ""))]
        if keys and parsed_scls[keys[0]]:
            return parsed_scls[keys[0]][0]['value']
        return None

    def _get_threshold(self, category: str) -> float:
        """Vrátí standardní klasifikační limit pro danou kategorii."""
        thresholds = {
            "Skin Corr. 1": SKIN_CORROSION_THRESHOLD_PERCENT,
            "Skin Irrit. 2": SKIN_IRRITATION_THRESHOLD_PERCENT,
            "Eye Dam. 1": EYE_DAMAGE_THRESHOLD_PERCENT,
            "Eye Irrit. 2": EYE_IRRITATION_THRESHOLD_PERCENT,
            "STOT SE 3": STOT_SE3_THRESHOLD_PERCENT,
        }
        return thresholds.get(category, STANDARD_CONCENTRATION_LIMITS.get(category, {}).get("cl", 100.0))

    def _get_cutoff(self, category: str, h_code: str) -> float:
        """Vrátí mezní hodnotu (cut-off) pro uvažování látky."""
        if any(x in category for x in ["Muta.", "Carc.", "Repr.", "ED HH"]):
            return CMR_CUTOFF_PERCENT
        if "Sens." in category:
            return SENSITISATION_CUTOFF_PERCENT
        if any(x in category for x in ["STOT SE 1", "STOT RE 1"]):
            return STOT_CATEGORY_1_CUTOFF_PERCENT
        return GENERAL_CUTOFF_PERCENT

    def _get_target_category(self, h_code: str, group: str) -> str:
        """Mapuje H-větu a skupinu na konkrétní výpočetní kategorii."""
        mapping = {
            ("H314", "Skin"): "Skin Corr. 1",
            ("H315", "Skin"): "Skin Irrit. 2",
            ("H318", "Eye"): "Eye Dam. 1",
            ("H319", "Eye"): "Eye Irrit. 2",
            ("H336", "STOT_SE"): "STOT SE 3 (Narcotic)",
        }
        res = mapping.get((h_code, group))
        if res: return res

        # Reprodukční toxicita a Akutní toxicita mají specifické sub-mappingy
        if group == "Repr":
            return "Repr. 1A" if h_code.startswith("H360") else "Repr. 2"
        
        # Fallback na CLP konstanty
        for cat_name, h in SCL_HAZARD_TO_H_CODE.items():
            if h == h_code and CAT_TO_GROUP.get(cat_name) == group:
                return cat_name
        return None

    # --- Evaluátory výsledků ---

    def _evaluate_skin_eye_hazards(self) -> None:
        """Vyhodnotí poleptání a podráždění kůže/očí pomocí sumační metody."""
        s1 = self.hazard_totals.get("Skin Corr. 1", {}).get("total", 0.0)
        s2 = self.hazard_totals.get("Skin Irrit. 2", {}).get("total", 0.0)
        
        # Skin Corr/Irrit
        if s1 >= SKIN_CORROSION_THRESHOLD_PERCENT or self.hazard_totals.get("Skin Corr. 1", {}).get("forced_by_scl"):
            self.health_hazards.add("H314")
            self.health_ghs.add("GHS05")
            self.log_entries.append({
                "step": "Skin Corr. 1",
                "detail": f"Sum Skin Corr. 1 = {s1:.2f}% >= {SKIN_CORROSION_THRESHOLD_PERCENT}% (nebo SCL)",
                "result": "H314"
            })
        else:
            self.log_entries.append({
                "step": "Skin Corr. 1",
                "detail": f"Sum Skin Corr. 1 = {s1:.2f}% < {SKIN_CORROSION_THRESHOLD_PERCENT}%",
                "result": "Neklasifikováno"
            })

        if (SKIN_CORROSION_WEIGHT_MULTIPLIER * s1 + s2) >= SKIN_IRRITATION_THRESHOLD_PERCENT:
            self.health_hazards.add("H315")
            self.health_ghs.add("GHS07")
            val = SKIN_CORROSION_WEIGHT_MULTIPLIER * s1 + s2
            self.log_entries.append({
                "step": "Skin Irrit. 2",
                "detail": f"Sum (10x Skin Corr. 1 + Skin Irrit. 2) = {val:.2f}% >= {SKIN_IRRITATION_THRESHOLD_PERCENT}%",
                "result": "H315"
            })
        elif "H314" not in self.health_hazards:
            val = SKIN_CORROSION_WEIGHT_MULTIPLIER * s1 + s2
            self.log_entries.append({
                "step": "Skin Irrit. 2",
                "detail": f"Sum (10x Skin Corr. 1 + Skin Irrit. 2) = {val:.2f}% < {SKIN_IRRITATION_THRESHOLD_PERCENT}%",
                "result": "Neklasifikováno"
            })

        # Eye Dam/Irrit (včetně příspěvku od Skin Corr)
        e1 = self.hazard_totals.get("Eye Dam. 1", {}).get("total", 0.0) + s1
        e2 = self.hazard_totals.get("Eye Irrit. 2", {}).get("total", 0.0)
        
        if e1 >= EYE_DAMAGE_THRESHOLD_PERCENT or self.hazard_totals.get("Eye Dam. 1", {}).get("forced_by_scl"):
            self.health_hazards.add("H318")
            self.health_ghs.add("GHS05")
            self.log_entries.append({
                "step": "Eye Dam. 1",
                "detail": f"Sum (Eye Dam. 1 + Skin Corr. 1) = {e1:.2f}% >= {EYE_DAMAGE_THRESHOLD_PERCENT}% (nebo SCL)",
                "result": "H318"
            })
        else:
            self.log_entries.append({
                "step": "Eye Dam. 1",
                "detail": f"Sum (Eye Dam. 1 + Skin Corr. 1) = {e1:.2f}% < {EYE_DAMAGE_THRESHOLD_PERCENT}%",
                "result": "Neklasifikováno"
            })

        if (EYE_DAMAGE_WEIGHT_MULTIPLIER * e1 + e2) >= EYE_IRRITATION_THRESHOLD_PERCENT:
            self.health_hazards.add("H319")
            self.health_ghs.add("GHS07")
            val = EYE_DAMAGE_WEIGHT_MULTIPLIER * e1 + e2
            self.log_entries.append({
                "step": "Eye Irrit. 2",
                "detail": f"Sum (10x Eye Dam. 1 + Eye Irrit. 2) = {val:.2f}% >= {EYE_IRRITATION_THRESHOLD_PERCENT}%",
                "result": "H319"
            })
        elif "H318" not in self.health_hazards:
            val = EYE_DAMAGE_WEIGHT_MULTIPLIER * e1 + e2
            self.log_entries.append({
                "step": "Eye Irrit. 2",
                "detail": f"Sum (10x Eye Dam. 1 + Eye Irrit. 2) = {val:.2f}% < {EYE_IRRITATION_THRESHOLD_PERCENT}%",
                "result": "Neklasifikováno"
            })

    def _evaluate_stot_se3(self) -> None:
        """Vyhodnotí STOT SE 3 příspěvky (H335 a H336 odděleně)."""
        # 1. H335 - Respiratory Irritation (uloženo pod "STOT SE 3")
        irr_data = self.hazard_totals.get("STOT SE 3", {})
        if irr_data.get("total", 0.0) >= STOT_SE3_THRESHOLD_PERCENT or irr_data.get("forced_by_scl"):
            self.health_hazards.add("H335")
            self.health_ghs.add("GHS07")
            self.log_entries.append({
                "step": "STOT SE 3 (Resp.)",
                "detail": f"Sum = {irr_data.get('total', 0.0):.2f}% >= {STOT_SE3_THRESHOLD_PERCENT}%",
                "result": "H335"
            })
        elif irr_data.get("total", 0.0) > 0:
            self.log_entries.append({
                "step": "STOT SE 3 (Resp.)",
                "detail": f"Sum = {irr_data.get('total', 0.0):.2f}% < {STOT_SE3_THRESHOLD_PERCENT}%",
                "result": "Neklasifikováno"
            })

        # 2. H336 - Narcotic Effects (uloženo pod "STOT SE 3 (Narcotic)")
        narc_data = self.hazard_totals.get("STOT SE 3 (Narcotic)", {})
        if narc_data.get("total", 0.0) >= STOT_SE3_THRESHOLD_PERCENT or narc_data.get("forced_by_scl"):
            self.health_hazards.add("H336")
            self.health_ghs.add("GHS07")
            self.log_entries.append({
                "step": "STOT SE 3 (Narc.)",
                "detail": f"Sum = {narc_data.get('total', 0.0):.2f}% >= {STOT_SE3_THRESHOLD_PERCENT}%",
                "result": "H336"
            })
        elif narc_data.get("total", 0.0) > 0:
             self.log_entries.append({
                "step": "STOT SE 3 (Narc.)",
                "detail": f"Sum = {narc_data.get('total', 0.0):.2f}% < {STOT_SE3_THRESHOLD_PERCENT}%",
                "result": "Neklasifikováno"
            })

    def _evaluate_aspiration_hazard(self) -> None:
        """Vyhodnotí nebezpečnost při vdechnutí (H304)."""
        # Suma koncentrací všech látek klasifikovaných jako H304
        h304_total = sum(
            c.concentration for c in self.components
            if c.substance.health_h_phrases and "H304" in c.substance.health_h_phrases
        )
        
        if h304_total >= ASPIRATION_HAZARD_THRESHOLD_PERCENT:
            self.health_hazards.add("H304")
            self.health_ghs.add("GHS08")
            self.log_entries.append({
                "step": "Aspiration Hazard",
                "detail": f"Suma H304 = {h304_total:.2f}% (Limit {ASPIRATION_HAZARD_THRESHOLD_PERCENT}%)",
                "result": "H304 (Asp. Tox. 1)"
            })

    def _evaluate_acute_toxicity_hazards(self) -> None:
        """Zpracuje kategorie Akutní toxicity (mimo ATEmix)."""
        cats = [
            ("Acute Tox. 3 (Dermal)", "H311", "GHS06"),
            ("Acute Tox. 4 (Dermal)", "H312", "GHS07"),
            ("Acute Tox. 3 (Oral)", "H301", "GHS06"),
            ("Acute Tox. 4 (Oral)", "H302", "GHS07"),
            ("Acute Tox. 3 (Inhalation)", "H331", "GHS06"),
            ("Acute Tox. 4 (Inhalation)", "H332", "GHS07"),
        ]
        for cat, h_code, ghs in cats:
            if self.hazard_totals.get(cat, {}).get("total", 0.0) > 0:
                self.health_hazards.add(h_code)
                self.health_ghs.add(ghs)
                # Logujeme pouze jako info, protože hlavní je ATE
                # Ale pokud to z nějakého důvodu (např. GCL/SCL na komponentě) projde,
                # chceme to vidět. Pozn: Toto většinou nenastane pro sumační metodu,
                # protože Acute Tox se počítá přes ATE. Ale kdyby...
                self.log_entries.append({
                    "step": f"Acute Tox ({cat})",
                    "detail": f"Detekována složka s {cat} (nespočítáno přes ATE?)",
                    "result": h_code
                })

    def _evaluate_generic_hazards(self) -> None:
        """Vyhodnotí neaditivní hazardy (CMR, STOT RE, atd.)."""
        # Tyto kategorie jsou řešeny vlastními metodami s aditivním přístupem
        # a nesmí být vyhodnoceny zde, protože hazard_totals obsahuje i podlimitní množství.
        excluded_prefixes = ("Skin Corr.", "Skin Irrit.", "Eye", "Aquatic", "STOT SE 3")
        
        for cat, data in self.hazard_totals.items():
            if cat.startswith(excluded_prefixes):
                continue

            if data["total"] > 0:
                h_code = SCL_HAZARD_TO_H_CODE.get(cat)
                if h_code and h_code not in self.health_hazards:
                    self.health_hazards.add(h_code)
                    ghs = SCL_HAZARD_TO_GHS_CODE.get(cat)
                    if ghs: self.health_ghs.add(ghs)
                    
                    contributors = self.hazard_totals[cat].get("contributors", [])
                    contrib_str = ", ".join(contributors)
                    self.log_entries.append({
                        "step": f"Hazard {cat}",
                        "detail": f"Obsahuje: {contrib_str}",
                        "result": h_code
                    })

    def _evaluate_modern_hazards(self) -> None:
        """Zpracuje Lactation a Endocrine Disruption (ED)."""
        # Lactation
        l_total = sum(c.concentration for c in self.components 
                      if c.substance.health_h_phrases and "H362" in c.substance.health_h_phrases)
        if l_total >= LACTATION_THRESHOLD_PERCENT:
            self.health_hazards.add("H362")
            self.log_entries.append({
                "step": "Lactation (H362)",
                "detail": f"Sum = {l_total:.2f}% >= {LACTATION_THRESHOLD_PERCENT}%",
                "result": "H362"
            })
        
        # ED HH (pomocí EUH vět)
        for c in self.components:
            if c.substance.ed_hh_cat == 1 and c.concentration >= ED_HH_CATEGORY_1_THRESHOLD_PERCENT:
                self.health_hazards.add("EUH430")
                self.log_entries.append({
                    "step": "Endocrine Disruptor HH 1",
                    "detail": f"{c.substance.name} >= {ED_HH_CATEGORY_1_THRESHOLD_PERCENT}%",
                    "result": "EUH430"
                })
            elif c.substance.ed_hh_cat == 2 and c.concentration >= ED_HH_CATEGORY_2_THRESHOLD_PERCENT:
                self.health_hazards.add("EUH431")
                self.log_entries.append({
                    "step": "Endocrine Disruptor HH 2",
                    "detail": f"{c.substance.name} >= {ED_HH_CATEGORY_2_THRESHOLD_PERCENT}%",
                    "result": "EUH431"
                })


def classify_by_concentration_limits(mixture: Mixture, components: Optional[List] = None):
    """Bridge funkce pro zachování kompatibility se stávajícím kódem."""
    classifier = HealthHazardClassifier(mixture, components=components)
    return classifier.classify()
