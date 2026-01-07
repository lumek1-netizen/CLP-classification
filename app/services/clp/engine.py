from typing import Tuple, Set, List, Optional
import json
from app.models import Mixture
from .ate import calculate_mixture_ate, classify_by_atemix
from .health import classify_by_concentration_limits
from .env import classify_environmental_hazards


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
    1. Akutní toxicita (ATEmix)
    2. Zdravotní nebezpečnost (koncentrační limity, aditivita)
    3. Nebezpečnost pro životní prostředí
    4. Sloučení výsledků, určení signálního slova a prioritizace symbolů (Článek 26).
    Výsledky jsou uloženy přímo do objektu směsi.
    """
    all_log = []

    try:
        # 1. ATEmix
        try:
            atemix_results, ate_log = calculate_mixture_ate(mixture)
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
            health_h, health_ghs, health_log = classify_by_concentration_limits(mixture)
            all_log.extend(health_log)
        except Exception as e:
            health_h, health_ghs = set(), set()
            all_log.append(
                {"step": "Chyba Health", "detail": str(e), "result": "ERROR"}
            )

        # 3. Environment
        try:
            env_h, env_ghs, env_log = classify_environmental_hazards(mixture)
            all_log.extend(env_log)
        except Exception as e:
            env_h, env_ghs = set(), set()
            all_log.append({"step": "Chyba Env", "detail": str(e), "result": "ERROR"})

        # Merge results
        total_h = ate_h | health_h | env_h
        total_ghs = ate_ghs | health_ghs | env_ghs

        # 4. EUH Phrases
        from .euh import classify_euh_phrases
        try:
            euh_h, euh_log = classify_euh_phrases(mixture, total_h, env_h) # Předáváme i env_h pro EUH210
            total_h |= euh_h
            all_log.extend(euh_log)
        except Exception as e:
            all_log.append({"step": "Chyba EUH", "detail": str(e), "result": "ERROR"})

        # Signal Word
        mixture.final_signal_word = get_signal_word(total_ghs, total_h)

        # Article 26 Priorities
        final_ghs = apply_article_26_priorities(total_ghs, total_h)

        # Save to model
        mixture.final_health_hazards = ", ".join(
            sorted([h for h in total_h if h.startswith("H3")])
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
