import pytest
from app.constants.clp import PhysicalState
from app.services.clp.ate import calculate_mixture_ate

# Mocks
class MockSubstance:
    def __init__(self, name, ate_dust=None):
        self.name = name
        self.ate_inhalation_dusts_mists = ate_dust
        self.ate_oral = None
        self.ate_dermal = None
        self.ate_inhalation_gases = None
        self.ate_inhalation_vapours = None
        self.health_h_phrases = ""

class MockComponent:
    def __init__(self, substance, concentration):
        self.substance = substance
        self.concentration = concentration

class MockMixture:
    def __init__(self, physical_state, components, can_generate_mist=False):
        self.physical_state = physical_state
        self.components = components
        self.can_generate_mist = can_generate_mist

def test_liquid_without_mist_flag():
    # Liquid, Mist Flag = False
    # Should IGNORE Dust/Mist ATE
    sub = MockSubstance("DustySub", ate_dust=1.5)
    comp = MockComponent(sub, 100)
    mix = MockMixture(PhysicalState.LIQUID, [comp], can_generate_mist=False)
    
    results, log = calculate_mixture_ate(mix)
    assert results.get('inhalation_dusts_mists') is None

def test_liquid_with_mist_flag():
    # Liquid, Mist Flag = True
    # Should CALCULATE Dust/Mist ATE
    sub = MockSubstance("DustySub", ate_dust=1.5)
    comp = MockComponent(sub, 100)
    mix = MockMixture(PhysicalState.LIQUID, [comp], can_generate_mist=True)
    
    results, log = calculate_mixture_ate(mix)
    val = results.get('inhalation_dusts_mists')
    assert val is not None
    assert abs(val - 1.5) < 0.01

def test_solid_always_calculates_dust():
    # Solid, Mist Flag = False (irrelevant for solid)
    # Should CALCULATE Dust/Mist ATE
    sub = MockSubstance("DustySub", ate_dust=1.5)
    comp = MockComponent(sub, 100)
    mix = MockMixture(PhysicalState.SOLID, [comp], can_generate_mist=False)
    
    results, log = calculate_mixture_ate(mix)
    assert results.get('inhalation_dusts_mists') is not None
