"""
Konstanty pro prahové hodnoty klasifikace podle CLP.

Tento modul obsahuje všechny numerické konstanty používané při klasifikaci směsí.
Centralizace konstant usnadňuje údržbu a zamezuje chybám z duplicitních hodnot.

Reference: Nařízení (ES) č. 1272/2008 (CLP) a novela 2023/707
"""

# ============================================================================
# SKIN & EYE HAZARDS - Poleptání a podráždění kůže a očí
# ============================================================================

# Skin Corrosion (Poleptání kůže)
SKIN_CORROSION_THRESHOLD_PERCENT = 5.0
"""Minimální koncentrace pro klasifikaci jako Skin Corr. 1 (H314)"""

SKIN_CORROSION_WEIGHT_MULTIPLIER = 10
"""Váhový multiplikátor pro Skin Corr. 1 při výpočtu Skin Irrit. 2"""

# Skin Irritation (Podráždění kůže)
SKIN_IRRITATION_THRESHOLD_PERCENT = 10.0
"""Minimální vážená koncentrace pro klasifikaci jako Skin Irrit. 2 (H315)"""

# Eye Damage (Vážné poškození očí)
EYE_DAMAGE_THRESHOLD_PERCENT = 3.0
"""Minimální koncentrace pro klasifikaci jako Eye Dam. 1 (H318)"""

EYE_DAMAGE_WEIGHT_MULTIPLIER = 10
"""Váhový multiplikátor pro Eye Dam. 1 při výpočtu Eye Irrit. 2"""

# Eye Irritation (Podráždění očí)
EYE_IRRITATION_THRESHOLD_PERCENT = 10.0
"""Minimální vážená koncentrace pro klasifikaci jako Eye Irrit. 2 (H319)"""


# ============================================================================
# RESPIRATORY HAZARDS - Dýchací cesty
# ============================================================================

# STOT SE 3 (Specific Target Organ Toxicity - Single Exposure)
STOT_SE3_THRESHOLD_PERCENT = 20.0
"""Minimální koncentrace pro klasifikaci jako STOT SE 3 (H335/H336)"""


# ============================================================================
# ASPIRATION HAZARD - Aspirační toxicita
# ============================================================================

ASPIRATION_HAZARD_THRESHOLD_PERCENT = 10.0
"""Minimální koncentrace pro klasifikaci jako Asp. Tox. 1 (H304)"""


# ============================================================================
# LACTATION - Účinky na laktaci
# ============================================================================

LACTATION_THRESHOLD_PERCENT = 0.3
"""Minimální koncentrace pro klasifikaci jako Lact. (H362)"""


# ============================================================================
# ENDOCRINE DISRUPTION - Endokrinní disrupce
# ============================================================================

ED_HH_CATEGORY_1_THRESHOLD_PERCENT = 0.1
"""Minimální koncentrace pro ED HH 1 (EUH430)"""

ED_HH_CATEGORY_2_THRESHOLD_PERCENT = 1.0
"""Minimální koncentrace pro ED HH 2 (EUH431)"""


# ============================================================================
# CMR HAZARDS - Karcinogenita, Mutagenita, Reprodukční toxicita
# ============================================================================

CMR_CUTOFF_PERCENT = 0.1
"""Cut-off limit pro CMR látky (Muta., Carc., Repr.)"""


# ============================================================================
# SENSITISATION - Senzibilizace
# ============================================================================

SENSITISATION_CUTOFF_PERCENT = 0.1
"""Cut-off limit pro senzibilizující látky (Resp. Sens., Skin Sens.)"""


# ============================================================================
# STOT CATEGORY 1 - Specifická toxicita pro cílové orgány kat. 1
# ============================================================================

STOT_CATEGORY_1_CUTOFF_PERCENT = 0.1
"""Cut-off limit pro STOT SE 1 a STOT RE 1"""


# ============================================================================
# AQUATIC HAZARDS - Nebezpečnost pro vodní prostředí
# ============================================================================

AQUATIC_ACUTE_1_CUTOFF_PERCENT = 0.1
"""Cut-off limit pro Aquatic Acute 1"""

AQUATIC_CHRONIC_1_CUTOFF_PERCENT = 0.1
"""Cut-off limit pro Aquatic Chronic 1"""

AQUATIC_THRESHOLD_PERCENT = 25.0
"""Standardní limit pro klasifikaci směsí jako Aquatic Acute/Chronic (25%)"""

AQUATIC_WEIGHT_FACTOR_10 = 10
"""Váhový faktor pro přepočet mezi kategoriemi (10x)"""

AQUATIC_WEIGHT_FACTOR_100 = 100
"""Váhový faktor pro přepočet mezi chronic 1 a chronic 3 (100x)"""


# ============================================================================
# GENERAL CUTOFF
# ============================================================================

GENERAL_CUTOFF_PERCENT = 1.0
"""Obecný cut-off limit pro ostatní třídy nebezpečnosti"""


# ============================================================================
# CONCENTRATION TOLERANCE
# ============================================================================

CONCENTRATION_SUM_TOLERANCE = 100.001
"""Tolerance pro součet koncentrací (kvůli zaokrouhlovacím chybám)"""
