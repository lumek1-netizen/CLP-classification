
import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp.health import classify_by_concentration_limits

def test_scenario_1_scl_masking_effect(app):
    """
    Scénář 1: 'Maskování GCL pomocí SCL'
    
    Látka A (3%): Skin Corr. 1B (H314), SCL Skin Corr. 1B >= 5%
    Látka B (8%): Skin Irrit. 2 (H315), bez SCL
    
    Očekáváme: Skin Irrit. 2 (H315)
    Důvod: Látka A (3%) má SCL pro Corr 1B, ale ne pro Irrit 2. 
           Pro Irrit 2 by měla přispívat standardně (nebo GCL). 
           Součet pro Irrit 2 = (10 * 3) + 8 = 38% >= 10%.
    """
    with app.app_context():
        # Setup
        sub_a = Substance(
            name="Substance A", 
            health_h_phrases="H314", # Skin Corr. 1B
            scl_limits="Skin Corr. 1B: >= 5.0"
        )
        sub_b = Substance(
            name="Substance B",
            health_h_phrases="H315" # Skin Irrit. 2
        )
        
        mixture = Mixture(name="Test Mixture 1")
        
        # Components
        # Note: In a real DB we'd add to session, but here we can just link objects if the service doesn't query DB directly but uses relationships.
        # Looking at health.py, it iterates mixture.components.
        
        comp_a = MixtureComponent(substance=sub_a, concentration=3.0)
        comp_b = MixtureComponent(substance=sub_b, concentration=8.0)
        
        mixture.components = [comp_a, comp_b]
        
        # Execute
        hazards, ghs, logs = classify_by_concentration_limits(mixture)
        
        # Assert
        # Current code likely fails this (returns empty set)
        assert "H315" in hazards, "Scenario 1 Failed: Should be classified as Skin Irrit. 2 (H315) due to additivity."
        assert "GHS07" in ghs


def test_scenario_2_additivity_bypass(app):
    """
    Scénář 2: 'Selhání aditivity u nízko-potentních látek'
    
    Látka A (40%): Skin Irrit. 2 (H315), SCL Skin Irrit. 2 >= 50%
    Látka B (9%): Skin Irrit. 2 (H315), bez SCL (GCL=10%)
    
    Očekáváme: Skin Irrit. 2 (H315)
    Důvod: Aditivní vzorec: Sum(Conc/Limit) >= 1.
           (40/50) + (9/10) = 0.8 + 0.9 = 1.7 >= 1.
    """
    with app.app_context():
        sub_a = Substance(
            name="Substance A (Low Potency)", 
            health_h_phrases="H315",
            scl_limits="Skin Irrit. 2: >= 50.0"
        )
        sub_b = Substance(
            name="Substance B (Standard)",
            health_h_phrases="H315"
        )
        
        mixture = Mixture(name="Test Mixture 2")
        comp_a = MixtureComponent(substance=sub_a, concentration=40.0)
        comp_b = MixtureComponent(substance=sub_b, concentration=9.0)
        mixture.components = [comp_a, comp_b]
        
        hazards, ghs, logs = classify_by_concentration_limits(mixture)
        
        assert "H315" in hazards, "Scenario 2 Failed: Should be classified as Skin Irrit. 2 (H315) due to weighted sum additivity."


def test_scenario_3_floating_point_abyss(app):
    """
    Scénář 3: 'Plovoucí desetiná propast'
    
    3 látky, každá 1.66666666666666% (Skin Corr 1A).
    Součet by měl být 5.0%.
    Limit pro Skin Corr 1 je >= 5.0%.
    """
    with app.app_context():
        sub = Substance(name="Corrosive Sub", health_h_phrases="H314") # Skin Corr. 1A/B/C generic H314
        
        mixture = Mixture(name="Test Mixture 3")
        
        # 5.0 / 3 = 1.6666666666666667
        conc = 5.0 / 3.0 
        
        comp_1 = MixtureComponent(substance=sub, concentration=conc)
        comp_2 = MixtureComponent(substance=sub, concentration=conc)
        comp_3 = MixtureComponent(substance=sub, concentration=conc)
        
        mixture.components = [comp_1, comp_2, comp_3]
        
        hazards, ghs, logs = classify_by_concentration_limits(mixture)
        
        assert "H314" in hazards, "Scenario 3 Failed: Should be classified as Skin Corr. 1 due to sum being exactly 5.0%."
