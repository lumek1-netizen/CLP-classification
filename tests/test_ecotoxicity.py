"""
Testy pro klasifikaci ekotoxicity podle LC50/EC50/NOEC.

Testuje funkce z app.services.clp.ecotoxicity podle kritérií CLP Přílohy I, část 4.1.
"""

import pytest
from app.services.clp.ecotoxicity import (
    assign_aquatic_acute_category,
    assign_aquatic_chronic_category,
    get_h_code_from_ecotoxicity,
    classify_substance_ecotoxicity
)


class TestAquaticAcuteClassification:
    """Testy pro Aquatic Acute kategorizaci."""
    
    def test_acute_cat1_lc50_fish(self):
        """LC50 ryby <= 1 mg/L -> Kategorie 1"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=0.5,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None
        )
        assert result == 1
    
    def test_acute_cat1_ec50_daphnia(self):
        """EC50 daphnie <= 1 mg/L -> Kategorie 1"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=None,
            ec50_daphnia_48h=0.8,
            ec50_algae_72h=None
        )
        assert result == 1
    
    def test_acute_cat1_ec50_algae(self):
        """EC50 řasy <= 1 mg/L -> Kategorie 1"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=None,
            ec50_daphnia_48h=None,
            ec50_algae_72h=1.0
        )
        assert result == 1
    
    def test_acute_cat1_multiple_values_min(self):
        """Min(LC50, EC50) <= 1 mg/L -> Kategorie 1"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=2.0,
            ec50_daphnia_48h=0.3,  # Nejnižší hodnota
            ec50_algae_72h=1.5
        )
        assert result == 1
    
    def test_acute_no_category_above_threshold(self):
        """Všechny hodnoty > 1 mg/L -> Žádná kategorie"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=5.0,
            ec50_daphnia_48h=3.0,
            ec50_algae_72h=4.0
        )
        assert result is None
    
    def test_acute_no_category_no_data(self):
        """Žádná data -> Žádná kategorie"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=None,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None
        )
        assert result is None
    
    def test_acute_boundary_value_exactly_1(self):
        """Hodnota přesně 1.0 mg/L -> Kategorie 1"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=1.0,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None
        )
        assert result == 1
    
    def test_acute_boundary_value_just_above_1(self):
        """Hodnota 1.01 mg/L -> Žádná kategorie"""
        result = assign_aquatic_acute_category(
            lc50_fish_96h=1.01,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None
        )
        assert result is None


class TestAquaticChronicClassification:
    """Testy pro Aquatic Chronic kategorizaci."""
    
    def test_chronic_cat1_lc50_not_degradable(self):
        """LC50 <= 1 mg/L, není rychle rozložitelná -> Kategorie 1"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=0.5,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=None,
            is_rapidly_degradable=False
        )
        assert result == 1
    
    def test_chronic_no_cat_when_rapidly_degradable(self):
        """LC50 <= 1 mg/L, ale je rychle rozložitelná -> Žádná kategorie (nebo nižší)"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=0.5,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=None,
            is_rapidly_degradable=True
        )
        assert result is None
    
    def test_chronic_cat2_ec50_range(self):
        """1 < EC50 <= 10 mg/L, není rychle rozložitelná -> Kategorie 2"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=None,
            ec50_daphnia_48h=5.0,
            ec50_algae_72h=None,
            noec_chronic=None,
            is_rapidly_degradable=False
        )
        assert result == 2
    
    def test_chronic_cat3_lc50_range(self):
        """10 < LC50 <= 100 mg/L, není rychle rozložitelná -> Kategorie 3"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=50.0,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=None,
            is_rapidly_degradable=False
        )
        assert result == 3
    
    def test_chronic_cat1_noec_below_01(self):
        """NOEC < 0.1 mg/L, není rychle rozložitelná -> Kategorie 1"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=None,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=0.05,
            is_rapidly_degradable=False
        )
        assert result == 1
    
    def test_chronic_cat2_noec_range(self):
        """0.1 <= NOEC <= 1 mg/L, není rychle rozložitelná -> Kategorie 2"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=None,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=0.5,
            is_rapidly_degradable=False
        )
        assert result == 2
    
    def test_chronic_cat3_noec_range(self):
        """1 < NOEC <= 10 mg/L, není rychle rozložitelná -> Kategorie 3"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=None,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=5.0,
            is_rapidly_degradable=False
        )
        assert result == 3
    
    def test_chronic_cat4_high_value_not_degradable(self):
        """LC50 > 100 mg/L, není rychle rozložitelná -> Kategorie 4"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=200.0,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=None,
            is_rapidly_degradable=False
        )
        assert result == 4
    
    def test_chronic_cat4_bioaccumulative(self):
        """LC50 > 100 mg/L, bioakumulativní -> Kategorie 4"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=150.0,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=None,
            is_rapidly_degradable=True,
            is_bioaccumulative=True
        )
        assert result == 4
    
    def test_chronic_uses_minimum_value(self):
        """Použije nejnižší hodnotu pro klasifikaci"""
        result = assign_aquatic_chronic_category(
            lc50_fish_96h=50.0,  # Cat 3
            ec50_daphnia_48h=0.5,  # Cat 1 - nejnižší
            ec50_algae_72h=8.0,  # Cat 2
            noec_chronic=None,
            is_rapidly_degradable=False
        )
        assert result == 1


class TestHCodeAssignment:
    """Testy pro přiřazení H-kódů a GHS piktogramů."""
    
    def test_acute_h400_ghs09(self):
        """Acute Cat 1 -> H400 + GHS09"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=1, chronic_category=None)
        assert "H400" in h_codes
        assert "GHS09" in ghs
    
    def test_chronic_cat1_h410_ghs09(self):
        """Chronic Cat 1 -> H410 + GHS09"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=1)
        assert "H410" in h_codes
        assert "GHS09" in ghs
    
    def test_chronic_cat2_h411_ghs09(self):
        """Chronic Cat 2 -> H411 + GHS09"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=2)
        assert "H411" in h_codes
        assert "GHS09" in ghs
    
    def test_chronic_cat3_h412_no_ghs(self):
        """Chronic Cat 3 -> H412 (bez GHS09)"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=3)
        assert "H412" in h_codes
        assert "GHS09" not in ghs
    
    def test_chronic_cat4_h413_no_ghs(self):
        """Chronic Cat 4 -> H413 (bez piktogramu)"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=4)
        assert "H413" in h_codes
        assert len(ghs) == 0
    
    def test_both_acute_and_chronic(self):
        """Acute 1 + Chronic 1 -> H400 + H410 + GHS09"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=1, chronic_category=1)
        assert "H400" in h_codes
        assert "H410" in h_codes
        assert "GHS09" in ghs
    
    def test_no_categories(self):
        """Žádné kategorie -> prázdné sety"""
        h_codes, ghs = get_h_code_from_ecotoxicity(acute_category=None, chronic_category=None)
        assert len(h_codes) == 0
        assert len(ghs) == 0


class TestCompleteClassification:
    """Testy pro kompletní klasifikaci látky."""
    
    def test_complete_classification_high_acute_toxicity(self):
        """Látka s vysokou akutní toxicitou"""
        result = classify_substance_ecotoxicity(
            lc50_fish_96h=0.3,
            ec50_daphnia_48h=0.5,
            ec50_algae_72h=0.2,
            noec_chronic=None,
            is_rapidly_degradable=False
        )
        
        assert result["acute_category"] == 1
        assert result["chronic_category"] == 1
        assert "H400" in result["h_codes"]
        assert "H410" in result["h_codes"]
        assert "GHS09" in result["ghs_codes"]
        assert "0.2" in result["classification_basis"]  # Nejnižší hodnota
    
    def test_complete_classification_only_noec(self):
        """Klasifikace pouze na základě NOEC"""
        result = classify_substance_ecotoxicity(
            lc50_fish_96h=None,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=0.08,
            is_rapidly_degradable=False
        )
        
        assert result["acute_category"] is None
        assert result["chronic_category"] == 1
        assert "H410" in result["h_codes"]
    
    def test_complete_classification_no_data(self):
        """Žádná data -> žádná klasifikace"""
        result = classify_substance_ecotoxicity(
            lc50_fish_96h=None,
            ec50_daphnia_48h=None,
            ec50_algae_72h=None,
            noec_chronic=None
        )
        
        assert result["acute_category"] is None
        assert result["chronic_category"] is None
        assert len(result["h_codes"]) == 0
        assert len(result["ghs_codes"]) == 0
        assert "Žádná ekotoxická data" in result["classification_basis"]
    
    def test_classification_basis_contains_all_values(self):
        """Klasifikační základ obsahuje všechny zadané hodnoty"""
        result = classify_substance_ecotoxicity(
            lc50_fish_96h=1.5,
            ec50_daphnia_48h=2.0,
            ec50_algae_72h=0.8,
            noec_chronic=0.05
        )
        
        basis = result["classification_basis"]
        assert "1.5" in basis
        assert "2.0" in basis
        assert "0.8" in basis
        assert "0.05" in basis


class TestRealWorldScenarios:
    """Testy s reálnými scénáři podle ECHA guidance."""
    
    def test_copper_sulfate_example(self):
        """
        Síran měďnatý (příklad z ECHA):
        - LC50 (ryby, 96h): 0.3 mg/L
        - EC50 (daphnie, 48h): 0.18 mg/L
        -> Aquatic Acute 1, Aquatic Chronic 1
        """
        result = classify_substance_ecotoxicity(
            lc50_fish_96h=0.3,
            ec50_daphnia_48h=0.18,
            is_rapidly_degradable=False
        )
        
        assert result["acute_category"] == 1
        assert result["chronic_category"] == 1
        assert "H400" in result["h_codes"]
        assert "H410" in result["h_codes"]
    
    def test_moderately_toxic_substance(self):
        """
        Středně toxická látka:
        - LC50 (ryby, 96h): 15 mg/L
        -> Aquatic Chronic 3 (10 < LC50 ≤ 100, pokud není rychle rozložitelná)
        """
        result = classify_substance_ecotoxicity(
            lc50_fish_96h=15.0,
            is_rapidly_degradable=False
        )
        
        assert result["acute_category"] is None
        assert result["chronic_category"] == 3
        assert "H412" in result["h_codes"]
    
    def test_low_toxicity_substance(self):
        """
        Nízko toxická látka:
        - LC50 (ryby, 96h): 75 mg/L
        -> Aquatic Chronic 3
        """
        result = classify_substance_ecotoxicity(
            lc50_fish_96h=75.0,
            is_rapidly_degradable=False
        )
        
        assert result["acute_category"] is None
        assert result["chronic_category"] == 3
        assert "H412" in result["h_codes"]
