from typing import Dict, List, Tuple, Optional, Set
from app.models import Mixture
from app.constants.clp import ATE_LIMITS, ATE_POINT_ESTIMATES, ACUTE_TOXICITY_MAP

class ATECalculator:
    """
    Kalkulátor pro výpočet odhadu akutní toxicity (ATEmix) a následnou klasifikaci.
    Implementuje vzorce podle Přílohy I, bod 3.1.3.6 nařízení CLP.
    """

    ROUTE_NAMES_CZ = {
        "oral": "Orální",
        "dermal": "Dermální",
        "inhalation_gases": "Inhalační (plyny)",
        "inhalation_vapours": "Inhalační (páry)",
        "inhalation_dusts_mists": "Inhalační (prach/mlha)",
    }

    # Mapa H-vět na kategorie pro bodové odhady
    H_TO_CAT_MAP = {
        "oral": {"H300": 2, "H301": 3, "H302": 4},
        "dermal": {"H310": 2, "H311": 3, "H312": 4},
        "gas": {"H330": 2, "H331": 3, "H332": 4},
        "vapour": {"H330": 2, "H331": 3, "H332": 4},
        "dust_mist": {"H330": 2, "H331": 3, "H332": 4},
    }

    def __init__(self, mixture: Mixture, components: Optional[List] = None):
        self.mixture = mixture
        self.components = components if components is not None else mixture.components
        self.log_entries: List[Dict[str, str]] = []
        self.atemix_results: Dict[str, Optional[float]] = {}
        
        # Mezisoučty pro sumaci (suma Ci / ATEi)
        self._sums = {k: 0.0 for k in self.ROUTE_NAMES_CZ.keys()}
        self._details = {k: [] for k in self.ROUTE_NAMES_CZ.keys()}
        
        self.allowed_routes = self._determine_allowed_routes()

    def calculate_and_classify(self) -> Tuple[Set[str], Set[str], List[Dict[str, str]]]:
        """Hlavní metoda pro výpočet ATEmix a přiřazení klasifikace."""
        try:
            self._calculate_atemix_values()
            return self._perform_classification()
        except Exception as e:
            return (
                set(),
                set(),
                [{"step": "CHYBA ATE", "detail": str(e), "result": "Selhání výpočtu"}],
            )

    def _determine_allowed_routes(self) -> Set[str]:
        """Určí relevantní cesty expozice na základě skupenství směsi."""
        phys_state = self.mixture.physical_state
        if not phys_state:
            return set(self.ROUTE_NAMES_CZ.keys())

        state_val = phys_state.value if hasattr(phys_state, "value") else str(phys_state)
        
        if state_val == "gas":
            return {"dermal", "inhalation_gases"}
        
        if state_val == "liquid":
            routes = {"oral", "dermal", "inhalation_vapours"}
            if self.mixture.can_generate_mist:
                routes.add("inhalation_dusts_mists")
            return routes
            
        if state_val == "solid":
            return {"oral", "dermal", "inhalation_dusts_mists"}
            
        return set(self.ROUTE_NAMES_CZ.keys())

    def _calculate_atemix_values(self) -> None:
        """Vypočítá hodnoty ATEmix pro každou povolenou cestu expozice."""
        for component in self.components:
            self._process_component(component)

        for route, sum_val in self._sums.items():
            if sum_val > 0:
                ate_mix = 100.0 / sum_val
                self.atemix_results[route] = ate_mix
                self._log_calculation(route, ate_mix)
            else:
                self.atemix_results[route] = None

    def _process_component(self, component) -> None:
        """Zpracuje příspěvek jedné složky do všech relevantních ATE sum."""
        substance = component.substance
        conc = component.concentration
        h_phrases = substance.health_h_phrases or ""

        # Mapování polí modelu na typy cest expozice
        routes_to_process = {
            "oral": ("oral", substance.ate_oral),
            "dermal": ("dermal", substance.ate_dermal),
            "inhalation_gases": ("gas", substance.ate_inhalation_gases),
            "inhalation_vapours": ("vapour", substance.ate_inhalation_vapours),
            "inhalation_dusts_mists": ("dust_mist", substance.ate_inhalation_dusts_mists),
        }

        for key, (route_type, val) in routes_to_process.items():
            if key not in self.allowed_routes:
                continue

            ate_val, source = self._get_best_ate_value(val, route_type, h_phrases)
            if ate_val:
                self._sums[key] += conc / ate_val
                self._details[key].append(f"{substance.name}: {conc}% / {ate_val} ({source})")

    def _get_best_ate_value(self, val: Optional[float], route_type: str, h_phrases: str) -> Tuple[Optional[float], Optional[str]]:
        """Vrátí buď naměřenou hodnotu ATE, nebo bodový odhad na základě H-vět."""
        if val is not None and val > 0:
            return val, "hodnota"

        # Zkusit bodový odhad podle H-vět
        h_map = self.H_TO_CAT_MAP.get(route_type, {})
        for h_code, cat in h_map.items():
            if h_code in h_phrases:
                estimate = ATE_POINT_ESTIMATES.get(route_type, {}).get(cat)
                if estimate:
                    return estimate, f"odhad ({h_code})"
        
        return None, None

    def _perform_classification(self) -> Tuple[Set[str], Set[str], List[Dict[str, str]]]:
        """Přiřadí výsledné H-věty a piktogramy GHS na základě vypočítaných ATEmix."""
        final_hazards: Set[str] = set()
        final_ghs: Set[str] = set()

        for route, ate_val in self.atemix_results.items():
            if ate_val is None:
                continue

            cat = self._determine_category(ate_val, route)
            route_cz = self.ROUTE_NAMES_CZ.get(route, route)
            
            log_msg = f"Hodnota {ate_val:.3f} -> Kategorie {cat}"
            
            if cat <= 4:
                h_code, ghs = self._get_classification_output(cat, route)
                if h_code and ghs:
                    final_hazards.add(h_code)
                    final_ghs.add(ghs)
                    log_msg += f" (Přiřazeno {h_code}, {ghs})"
            else:
                log_msg += " (Neklasifikováno)"

            self.log_entries.append({"step": f"Klasifikace ATE - {route_cz}", "detail": log_msg, "result": "OK"})

        return final_hazards, final_ghs, self.log_entries

    def _determine_category(self, ate_val: float, route: str) -> int:
        """Najde kategorii (1-4) podle tabulky limitů v CLP."""
        # Normalizace názvu cesty pro lookup v ATE_LIMITS
        norm_map = {"oral": "oral", "dermal": "dermal", "gas": "gas", "vapour": "vapour", "dust": "dust_mist", "mist": "dust_mist"}
        norm_route = next((v for k, v in norm_map.items() if k in route), "oral")
        
        limits = ATE_LIMITS.get(norm_route, [])
        for i, limit in enumerate(limits):
            if ate_val <= limit:
                return i + 1
        return 5

    def _get_classification_output(self, cat: int, route: str) -> Tuple[Optional[str], Optional[str]]:
        """Vrátí H-větu a GHS kód pro danou kategorii a cestu expozice."""
        info = ACUTE_TOXICITY_MAP.get(cat)
        if not info:
            return None, None
            
        suffix = {1: 0, 2: 0, 3: 1, 4: 2}.get(cat, 2)
        
        if "oral" in route: h_code = f"H30{suffix}"
        elif "dermal" in route: h_code = f"H31{suffix}"
        else: h_code = f"H33{suffix}" # Inhalační cesty
        
        return h_code, info["ghs"]

    def _log_calculation(self, route: str, val: float) -> None:
        """Vytvoří záznam o výpočtu do logu."""
        route_cz = self.ROUTE_NAMES_CZ.get(route, route)
        calc_str = " + ".join(self._details[route])
        self.log_entries.append({
            "step": f"Výpočet ATEmix - {route_cz}",
            "detail": f"100 / ({calc_str})",
            "result": f"ATEmix = {val:.2f}"
        })


# --- Legacy Bridge Functions ---

def calculate_mixture_ate(mixture: Mixture, components: Optional[List] = None):
    """Bridge pro zachování kompatibility s existujícím voláním."""
    calc = ATECalculator(mixture, components=components)
    # Pro zpětnou kompatibilitu s calculate_mixture_ate v engine.py
    # tato funkce historicky vracela (results, logs).
    calc._calculate_atemix_values()
    return calc.atemix_results, calc.log_entries

def classify_by_atemix(atemix_results: Dict[str, Optional[float]]):
    """Bridge pro klasifikaci z hotových výsledků."""
    # Toto je složitější bridge, protože původní kód byl rozdělen.
    # Pro jednoduchost vytvoříme dummy instanci.
    dummy_mix = Mixture(name="Bridge")
    calc = ATECalculator(dummy_mix)
    calc.atemix_results = atemix_results
    return calc._perform_classification()

def _determine_ate_category(ate_val: float, route: str) -> int:
    """Bridge pro unit testy."""
    dummy_mix = Mixture(name="Bridge")
    calc = ATECalculator(dummy_mix)
    return calc._determine_category(ate_val, route)
