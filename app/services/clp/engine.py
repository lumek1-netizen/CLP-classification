"""
Hlavní výpočetní engine pro CLP klasifikaci.

Tento modul orchestrace celý proces klasifikace směsi.
Volá dílčí kalkulátory (ATE, Health, Env, Physical) a agreguje výsledky.
Implementuje také prioritní pravidla pro označování (Článek 26).
"""

from typing import Tuple, Set, List, Optional
import json
from app.models import Mixture
from .ate import calculate_mixture_ate, classify_by_atemix
from .health import classify_by_concentration_limits
from .env import classify_environmental_hazards
from .physical import evaluate_flammable_liquids
from .p_phrases import assign_p_phrases


def get_signal_word(ghs_codes: Set, h_phrases: Set = None) -> Optional[str]:
    """
    Určí signální slovo (NEBEZPEČÍ / VAROVÁNÍ) na základě výsledných GHS kódů a H-vět.
    DANGER má přednost před WARNING.
    """
    if not h_phrases:
        h_phrases = set()

    # Priority: DANGER > WARNING > None
    danger_h = [
        "H300",
        "H310",
        "H330",
        "H301",
        "H311",
        "H331",
        "H314",
        "H318",
        "H334",
        "H340",
        "H350",
        "H360",
        "H370",
        "H372",
        "H224",
        "H225",
    ]
    if (
        any(h in h_phrases for h in danger_h)
        or "GHS06" in ghs_codes
        or "GHS05" in ghs_codes
    ):
        return "NEBEZPEČÍ"

    warning_h = [
        "H302",
        "H312",
        "H332",
        "H315",
        "H319",
        "H317",
        "H341",
        "H351",
        "H361",
        "H371",
        "H373",
        "H335",
        "H336",
        "H226",
    ]
    if (
        any(h in h_phrases for h in warning_h)
        or "GHS07" in ghs_codes
        or "GHS08" in ghs_codes
    ):
        return "VAROVÁNÍ"

    return None


def apply_article_26_priorities(ghs_codes: Set, h_phrases: Set) -> Set:
    """Uplatňuje zásady priority pro výstražné symboly (Článek 26 CLP)."""
    ghs = set(ghs_codes)
    if "GHS06" in ghs:
        ghs.discard("GHS07")
    if "GHS05" in ghs and any(h in h_phrases for h in ["H315", "H319"]):
        ghs.discard("GHS07")
    if (
        "GHS08" in ghs
        and "H334" in h_phrases
        and any(h in h_phrases for h in ["H317", "H315", "H319"])
    ):
        ghs.discard("GHS07")
    return ghs


def run_clp_classification(mixture: Mixture) -> None:
    """
    Hlavní orchestrátor klasifikace CLP. 
    Provádí výpočty v krocích:
    1. Rozbalení směsí na jednotlivé látky (pokud směs obsahuje jiné směsi)
    2. Akutní toxicita (ATEmix)
    3. Zdravotní nebezpečnost (koncentrační limity, aditivita)
    4. Nebezpečnost pro životní prostředí
    5. Sloučení výsledků, určení signálního slova a prioritizace symbolů (Článek 26).
    Výsledky jsou uloženy přímo do objektu směsi.
    """
    all_log = []

    try:
        # 0. Rozbalit směsi na látky (pokud směs obsahuje jiné směsi)
        from app.models import ComponentType
        from app.services.mixture_service import MixtureService
        
        # Získat seznam komponent pro výpočet (buď originální, nebo rozbalené)
        calc_components = mixture.components
        
        has_mixture_components = False
        for comp in mixture.components:
            # Robustnější kontrola typu: zvládne Enum i řetězec z DB
            if (comp.component_type == ComponentType.MIXTURE or 
                str(comp.component_type).lower() == "componenttype.mixture" or
                str(comp.component_type).lower() == "mixture"):
                has_mixture_components = True
                break
        
        if has_mixture_components:
            # Rozbalit směsi na látky
            expanded_substances = MixtureService.expand_mixture_components(mixture.id)
            
            # Vytvoříme dočasné komponenty pouze s látkami
            from app.models import Substance
            temp_components = []
            for exp in expanded_substances:
                # Vytvoříme dočasný objekt podobný MixtureComponent
                class TempComponent:
                    def __init__(self, substance_id, concentration):
                        self.substance_id = substance_id
                        self.concentration = concentration
                        self.component_type = ComponentType.SUBSTANCE
                        self.substance = Substance.query.get(substance_id)
                
                if exp.get('substance_id'):
                    temp_components.append(
                        TempComponent(exp['substance_id'], exp['concentration'])
                    )
            
            # Pro výpočet použijeme rozbalené komponenty
            calc_components = temp_components
            
            all_log.append({
                "step": "Rozbalení směsí",
                "detail": f"Rozbaleno na {len(temp_components)} látek z vnořených směsí",
                "result": "OK"
            })
        else:
            all_log.append({
                "step": "Rozbalení směsí",
                "detail": "Směs neobsahuje vnořené směsi, rozbalení není nutné",
                "result": "SKIP"
            })
        
        # Funkce v modulech ate, health, env bohužel očekávají mixture.components
        # Musíme dočasně "podvrhnout" komponenty směsi bez vyvolání smazání v DB
        # To uděláme tak, že budeme klasifikačním funkcím předávat calc_components, 
        # pokud to umožňují, nebo dočasně modifikujeme objekt mixture jen v paměti.
        # Nejbezpečnější pro stávající architekturu je přidat argument components do funkcí.
        # Ale to by vyžadovalo změnu mnoha souborů.
        # Zkusíme dočasně nahradit mixture.components tak, aby to SQLAlchemy nepovažovala za změnu vztahu.
        
        original_components = mixture.components
        
        # Místo přímého zásahu do relationship zkusíme vytvořit "virtuální" směs pro výpočet
        # nebo upravíme funkce, aby braly seznam komponent.
        
        # 1. ATEmix
        try:
            from .ate import calculate_mixture_ate, classify_by_atemix
            atemix_results, ate_log = calculate_mixture_ate(mixture, components=calc_components)
            all_log.extend(ate_log)


            # Update mixture properties
            mixture.final_atemix_oral = atemix_results.get("oral")
            mixture.final_atemix_dermal = atemix_results.get("dermal")
            mixture.final_atemix_inhalation = next(
                (
                    v
                    for v in [
                        atemix_results.get("inhalation_vapours"),
                        atemix_results.get("inhalation_dusts_mists"),
                        atemix_results.get("inhalation_gases"),
                    ]
                    if v is not None
                ),
                None,
            )

            ate_h, ate_ghs, ate_class_log = classify_by_atemix(atemix_results)
            all_log.extend(ate_class_log)
        except Exception as e:
            ate_h, ate_ghs = set(), set()
            all_log.append({"step": "Chyba ATE", "detail": str(e), "result": "ERROR"})

        # 2. Health (Concentration Limits)
        try:
            health_h, health_ghs, health_log = classify_by_concentration_limits(mixture, components=calc_components)
            all_log.extend(health_log)
        except Exception as e:
            health_h, health_ghs = set(), set()
            all_log.append(
                {"step": "Chyba Health", "detail": str(e), "result": "ERROR"}
            )

        # 3. Environment
        try:
            env_h, env_ghs, env_log = classify_environmental_hazards(mixture, components=calc_components)
            all_log.extend(env_log)
        except Exception as e:
            env_h, env_ghs = set(), set()
            all_log.append({"step": "Chyba Env", "detail": str(e), "result": "ERROR"})

        # 3.5 Physical Hazards
        phys_h, phys_ghs = set(), set()
        try:
            if mixture.physical_state and hasattr(mixture.physical_state, 'value') and mixture.physical_state.value == 'liquid':
                 phys_h, phys_ghs, phys_log = evaluate_flammable_liquids(mixture.flash_point, mixture.boiling_point)
                 all_log.extend(phys_log)
        except Exception as e:
             all_log.append({"step": "Chyba Fyzikální", "detail": str(e), "result": "ERROR"})
        
        # Merge results
        total_h = ate_h | health_h | env_h | phys_h
        total_ghs = ate_ghs | health_ghs | env_ghs | phys_ghs

        # 4. EUH Phrases
        from .euh import classify_euh_phrases
        try:
            euh_h, euh_log = classify_euh_phrases(mixture, total_h, env_h, components=calc_components)
            total_h |= euh_h
            all_log.extend(euh_log)
        except Exception as e:
            all_log.append({"step": "Chyba EUH", "detail": str(e), "result": "ERROR"})

        # Signal Word
        mixture.final_signal_word = get_signal_word(total_ghs, total_h)

        # Article 26 Priorities
        final_ghs = apply_article_26_priorities(total_ghs, total_h)

        # P-Phrases
        final_p_codes = assign_p_phrases(total_h, mixture.user_type)
        mixture.final_precautionary_statements = ", ".join(final_p_codes)

        # Save to model
        mixture.final_health_hazards = ", ".join(
            sorted([h for h in total_h if h.startswith("H3")])
        )
        mixture.final_physical_hazards = ", ".join(
            sorted([h for h in total_h if h.startswith("H2")])
        )
        mixture.final_environmental_hazards = ", ".join(
            sorted([h for h in total_h if h.startswith("H4")])
        )
        mixture.final_ghs_codes = ", ".join(sorted(final_ghs))
        mixture.classification_log = all_log

    except Exception as e:
        # Fallback pro kritickou chybu v orchestrátoru
        all_log.append({"step": "Kritická chyba", "detail": str(e), "result": "FATAL"})
        mixture.classification_log = all_log
