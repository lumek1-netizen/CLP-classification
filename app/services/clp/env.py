from typing import Dict, List, Tuple, Set, Any, Optional
from app.models import Mixture
from .scl import parse_scls, evaluate_scl_condition
from .ecotoxicity import classify_substance_ecotoxicity
from app.constants.classification_thresholds import (
    AQUATIC_THRESHOLD_PERCENT,
    AQUATIC_WEIGHT_FACTOR_10,
    AQUATIC_WEIGHT_FACTOR_100,
    AQUATIC_ACUTE_1_CUTOFF_PERCENT,
    AQUATIC_CHRONIC_1_CUTOFF_PERCENT,
    GENERAL_CUTOFF_PERCENT,
)

class EnvironmentalHazardClassifier:
    """
    Kalkulátor pro klasifikaci nebezpečnosti směsi pro životní prostředí.
    Implementuje aditivní metodu a nová pravidla 2026 (Ozone, ED ENV, PBT/PMT).
    """

    def __init__(self, mixture: Mixture, components: Optional[List] = None):
        self.mixture = mixture
        self.components = components if components is not None else mixture.components
        
        # Mezisoučty pro aditivitu
        self.sum_acute_1 = 0.0
        self.sum_chronic_1 = 0.0
        self.sum_chronic_2 = 0.0
        self.sum_chronic_3 = 0.0
        self.sum_chronic_4 = 0.0
        
        # Evidence přispěvatelů (pro logování)
        self.contributors: Dict[str, List[str]] = {
            "acute_1": [], "chronic_1": [], "chronic_2": [], "chronic_3": [], "chronic_4": []
        }
        
        # Výsledky
        self.hazards: Set[str] = set()
        self.ghs: Set[str] = set()
        self.log_entries: List[Dict[str, str]] = []
        
        # Pomocné evidence pro nová pravidla
        self.ozone_names: List[str] = []
        self.ed_env_names: List[Tuple[str, int]] = []
        self.pbt_pmt_codes: Set[str] = set()
        self.unknown_toxicity_sum = 0.0
        
        self.processed_substances: Set[int] = set()

    def classify(self) -> Tuple[Set[str], Set[str], List[Dict[str, str]]]:
        """Hlavní metoda pro spuštění klasifikace životního prostředí."""
        try:
            self._process_all_components()
            
            # Evaluace kategorií (pořadí od nejzávažnější)
            self._evaluate_aquatic_acute()
            self._evaluate_aquatic_chronic()
            self._evaluate_ozone_hazard()
            self._evaluate_modern_hazards() # ED ENV, PBT/PMT
            self._finalize_unknown_toxicity()

            return self.hazards, self.ghs, self.log_entries
        except Exception as e:
            return (
                set(),
                set(),
                [{"step": "CHYBA", "detail": str(e), "result": "Selhání klasifikace ENV"}],
            )

    def _process_all_components(self) -> None:
        """Projde všechny složky směsi a shromáždí data pro výpočet."""
        for component in self.components:
            substance = component.substance
            conc = component.concentration
            sub_name = substance.name

            # 1. Priorita: Klasifikace na základě testovacích dat (LC50/EC50/NOEC)
            self._process_ecotoxicity_data(substance, conc)
            
            # 2. Fallback: Klasifikace na základě H-vět (pokud nebyla použita testovací data)
            if substance.id not in self.processed_substances:
                self._process_h_phrase_hazards(substance, conc)
            elif substance.env_h_phrases:
                self._log_skip_h_phrases(sub_name)

            # 3. Speciální třídy 2026 a neznámá toxicita
            self._track_modern_classes(substance, conc)
            self._check_for_unknown_toxicity(substance, conc)

    def _process_ecotoxicity_data(self, substance, conc) -> None:
        """Zpracuje primární ekotoxická data látky."""
        ecotox = classify_substance_ecotoxicity(
            lc50_fish_96h=substance.lc50_fish_96h,
            ec50_daphnia_48h=substance.ec50_daphnia_48h,
            ec50_algae_72h=substance.ec50_algae_72h,
            noec_chronic=substance.noec_chronic,
            is_rapidly_degradable=False,  # Zde bude v budoucnu napojeno na DB pole
            is_bioaccumulative=False
        )
        
        if ecotox["h_codes"]:
            self.processed_substances.add(substance.id)
            self._log_ecotox_basis(substance.name, conc, ecotox)
            self._add_ecotox_to_sums(substance, conc, ecotox)

    def _process_h_phrase_hazards(self, substance, conc) -> None:
        """Zpracuje nebezpečnost na základě H-vět a SCL."""
        if not substance.env_h_phrases and not substance.scl_limits:
            return

        scl_covered = self._apply_scl_limits(substance, conc)
        
        if substance.env_h_phrases:
            h_codes = [h.strip() for h in substance.env_h_phrases.split(",")]
            for h_code in h_codes:
                self._apply_gcl_contribution(substance, conc, h_code, scl_covered)

    def _apply_scl_limits(self, substance, conc) -> Set[str]:
        """Aplikuje specifické koncentrační limity (SCL) pro životní prostředí."""
        covered = set()
        if not substance.scl_limits:
            return covered

        parsed = parse_scls(substance.scl_limits)
        mapping = {
            "Aquatic Acute 1": ("H400", "acute_1", True),
            "Aquatic Chronic 1": ("H410", "chronic_1", True),
            "Aquatic Chronic 2": ("H411", "chronic_2", False),
            "Aquatic Chronic 3": ("H412", "chronic_3", False),
            "Aquatic Chronic 4": ("H413", "chronic_4", False),
        }

        for scl_cat, conditions in parsed.items():
            if evaluate_scl_condition(conc, conditions) and scl_cat in mapping:
                h_code, sum_key, force_ghs = mapping[scl_cat]
                self.hazards.add(h_code)
                if force_ghs: self.ghs.add("GHS09")
                
                self._log_scl_hit(scl_cat, substance.name, conc)
                
                # Přidání do sum (s M-faktorem u kategorie 1)
                m_factor = getattr(substance, f"m_factor_{sum_key.split('_')[0]}", 1) or 1
                self._update_sum(sum_key, conc, m_factor, substance.name)
                covered.add(scl_cat)
        
        return covered

    def _apply_gcl_contribution(self, substance, conc, h_code, scl_covered) -> None:
        """Aplikuje obecné koncentrační limity (GCL) pro životní prostředí."""
        rule_map = {
            "H400": ("Aquatic Acute 1", AQUATIC_ACUTE_1_CUTOFF_PERCENT, "acute_1"),
            "H410": ("Aquatic Chronic 1", AQUATIC_CHRONIC_1_CUTOFF_PERCENT, "chronic_1"),
            "H411": ("Aquatic Chronic 2", 1.0, "chronic_2"),
            "H412": ("Aquatic Chronic 3", 1.0, "chronic_3"),
            "H413": ("Aquatic Chronic 4", 1.0, "chronic_4"),
        }

        if h_code in rule_map:
            cat_name, cutoff, sum_key = rule_map[h_code]
            if cat_name not in scl_covered and conc >= cutoff:
                m_factor = getattr(substance, f"m_factor_{sum_key.split('_')[0]}", 1) or 1
                self._update_sum(sum_key, conc, m_factor, substance.name)

    def _update_sum(self, sum_key: str, conc: float, m_factor: int, name: str) -> None:
        """Pomocná metoda pro aktualizaci součtů a seznamů přispěvatelů."""
        weighted_conc = conc * m_factor
        setattr(self, f"sum_{sum_key}", getattr(self, f"sum_{sum_key}") + weighted_conc)
        
        note = f"{name} ({conc}% x M{m_factor})" if m_factor != 1 else f"{name} ({conc}%)"
        self.contributors[sum_key].append(note)

    # --- Evaluace výsledků ---

    def _evaluate_aquatic_acute(self) -> None:
        """Vyhodnotí Aquatic Acute 1."""
        if self.sum_acute_1 >= AQUATIC_THRESHOLD_PERCENT:
            self.hazards.add("H400")
            self.ghs.add("GHS09")
            self.log_entries.append({
                "step": "Aquatic Acute 1",
                "detail": f"Součet = {self.sum_acute_1} >= {AQUATIC_THRESHOLD_PERCENT}",
                "result": "H400"
            })

    def _evaluate_aquatic_chronic(self) -> None:
        """Vyhodnotí Aquatic Chronic 1-4 pomocí sumační metody."""
        # Chronic 1
        if self.sum_chronic_1 >= AQUATIC_THRESHOLD_PERCENT:
            self.hazards.add("H410")
            self.ghs.add("GHS09")
            self.log_entries.append({
                "step": "Aquatic Chronic 1",
                "detail": f"Součet = {self.sum_chronic_1} >= {AQUATIC_THRESHOLD_PERCENT}",
                "result": "H410"
            })

        # Chronic 2 (Vážený součet)
        val_c2 = (AQUATIC_WEIGHT_FACTOR_10 * self.sum_chronic_1) + self.sum_chronic_2
        if val_c2 >= AQUATIC_THRESHOLD_PERCENT:
            if "H410" not in self.hazards:
                self.hazards.add("H411")
                self.ghs.add("GHS09")
            self._log_vaha("Chronic 2", val_c2, "H411")

        # Chronic 3 (Vážený součet)
        val_c3 = (AQUATIC_WEIGHT_FACTOR_100 * self.sum_chronic_1) + \
                 (AQUATIC_WEIGHT_FACTOR_10 * self.sum_chronic_2) + self.sum_chronic_3
        if val_c3 >= AQUATIC_THRESHOLD_PERCENT:
            if not any(h in self.hazards for h in ["H410", "H411"]):
                self.hazards.add("H412")
            self._log_vaha("Chronic 3", val_c3, "H412")

        # Chronic 4
        sum_total = self.sum_chronic_1 + self.sum_chronic_2 + self.sum_chronic_3 + self.sum_chronic_4
        if sum_total >= AQUATIC_THRESHOLD_PERCENT:
            if not any(h in self.hazards for h in ["H410", "H411", "H412"]):
                self.hazards.add("H413")
                self.log_entries.append({
                    "step": "Aquatic Chronic 4",
                    "detail": f"Součet k4 = {sum_total} >= {AQUATIC_THRESHOLD_PERCENT}",
                    "result": "H413"
                })

    def _evaluate_ozone_hazard(self) -> None:
        """Vyhodnotí nebezpečnost pro ozonovou vrstvu."""
        if self.ozone_names:
            self.hazards.add("H420")
            self.ghs.add("GHS07")
            self.log_entries.append({
                "step": "Ozone", "detail": f"Obsahuje: {', '.join(self.ozone_names)}", "result": "H420"
            })

    def _evaluate_modern_hazards(self) -> None:
        """Zpracuje ED ENV, PBT a PMT třídy (2026)."""
        for name, cat in self.ed_env_names:
            self.hazards.add("EUH440" if cat == 1 else "EUH441")
        self.hazards.update(self.pbt_pmt_codes)

    def _finalize_unknown_toxicity(self) -> None:
        """Dokončí výpočet neznámé toxicity a přidá záznam do logu."""
        self.mixture.unknown_env_toxicity_percent = self.unknown_toxicity_sum
        if self.unknown_toxicity_sum > 0:
            self.log_entries.append({
                "step": "Neznámá toxicita (Env)",
                "detail": f"Obsahuje {self.unknown_toxicity_sum:.2f} % neznámých složek.",
                "result": "INFO"
            })

    # --- Interní trackery a loggery ---

    def _track_modern_classes(self, substance, conc) -> None:
        """Sleduje přítomnost 2026 tříd nebezpečnosti."""
        if substance.env_h_phrases and "H420" in substance.env_h_phrases and conc >= 0.1:
            self.ozone_names.append(substance.name)
        
        if substance.ed_env_cat:
            limit = 0.1 if substance.ed_env_cat == 1 else 1.0
            if conc >= limit: self.ed_env_names.append((substance.name, substance.ed_env_cat))
        
        if conc >= 0.1:
            if substance.is_pbt or substance.is_vpvb: self.pbt_pmt_codes.add("EUH450")
            if substance.is_pmt or substance.is_vpvm: self.pbt_pmt_codes.add("EUH451")

    def _check_for_unknown_toxicity(self, substance, conc) -> None:
        """Zjišťuje, zda je látka považována za 'známou' pro životní prostředí."""
        is_known = any([
            substance.env_h_phrases,
            substance.scl_limits and "Aquatic" in substance.scl_limits,
            substance.ed_env_cat, substance.is_pbt, substance.is_vpvb,
            substance.is_pmt, substance.is_vpvm,
            substance.lc50_fish_96h, substance.ec50_daphnia_48h, 
            substance.ec50_algae_72h, substance.noec_chronic
        ])
        if not is_known:
            self.unknown_toxicity_sum += conc

    def _add_ecotox_to_sums(self, substance, conc, ecotox) -> None:
        """Přidá příspěvek z ekotoxických testů do aditivních součtů."""
        if ecotox["acute_category"] == 1 and conc >= AQUATIC_ACUTE_1_CUTOFF_PERCENT:
            self._update_sum("acute_1", conc, substance.m_factor_acute or 1, substance.name)
        
        cat = ecotox["chronic_category"]
        if cat:
            m = substance.m_factor_chronic or 1
            if cat == 1 and conc >= AQUATIC_CHRONIC_1_CUTOFF_PERCENT: self._update_sum("chronic_1", conc, m, substance.name)
            elif cat == 2 and conc >= GENERAL_CUTOFF_PERCENT: self._update_sum("chronic_2", conc, 1, substance.name)
            elif cat == 3 and conc >= GENERAL_CUTOFF_PERCENT: self._update_sum("chronic_3", conc, 1, substance.name)
            elif cat == 4 and conc >= GENERAL_CUTOFF_PERCENT: self._update_sum("chronic_4", conc, 1, substance.name)

    def _log_ecotox_basis(self, name, conc, ecotox) -> None:
        """Loguje základ klasifikace z ekotoxických dat."""
        for ctype in ["acute", "chronic"]:
            cat = ecotox[f"{ctype}_category"]
            if cat:
                self.log_entries.append({
                    "step": f"Ekotoxicita ({ctype.capitalize()} {cat})",
                    "detail": f"{name} ({conc}%): {ecotox['classification_basis']}",
                    "result": f"CAT {cat}"
                })

    def _log_skip_h_phrases(self, name: str) -> None:
        self.log_entries.append({"step": "Skip H-phrases", "detail": f"{name}: Data o testech mají přednost.", "result": "SKIP"})

    def _log_scl_hit(self, cat, name, conc) -> None:
        self.log_entries.append({"step": f"{cat} (SCL)", "detail": f"Mez pro {name} splněna ({conc}%)", "result": "SCL OK"})

    def _log_vaha(self, step: str, val: float, res: str) -> None:
        self.log_entries.append({"step": step, "detail": f"Vážený součet = {val:.2f} >= {AQUATIC_THRESHOLD_PERCENT}", "result": res})


def classify_environmental_hazards(mixture: Mixture, components: Optional[List] = None):
    """Bridge funkce pro zachování kompatibility."""
    classifier = EnvironmentalHazardClassifier(mixture, components=components)
    return classifier.classify()
