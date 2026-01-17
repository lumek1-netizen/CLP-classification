import pytest
from app.constants.clp import PhysicalState
from app.services.clp.ate import calculate_mixture_ate
from app.services.clp.physical import evaluate_flammable_liquids

# Mocks
class MockSubstance:
    def __init__(self, name, ate_oral=None, ate_gas=None):
        self.name = name
        self.ate_oral = ate_oral
        self.ate_inhalation_gases = ate_gas
        self.health_h_phrases = ""
        self.ate_dermal = None
        self.ate_inhalation_vapours = None
        self.ate_inhalation_dusts_mists = None

class MockComponent:
    def __init__(self, substance, concentration):
        self.substance = substance
        self.concentration = concentration

class MockMixture:
    def __init__(self, physical_state, components):
        self.physical_state = physical_state
        self.components = components

def test_ate_filtering_solid_ignore_gas():
    # Mixture is Solid, Component has Gas ATE
    # Should NOT calculate Gas ATE
    sub = MockSubstance("GasSub", ate_gas=100) # Cat 1/2 range
    comp = MockComponent(sub, 100)
    mix = MockMixture(PhysicalState.SOLID, [comp])
    
    results, log = calculate_mixture_ate(mix)
    
    # Inhalation gases should be None because mix is solid
    assert results['inhalation_gases'] is None

def test_ate_filtering_liquid_ignore_gas():
    # Mixture is Liquid, Component has Gas ATE
    # Should NOT calculate Gas ATE
    sub = MockSubstance("GasSub", ate_gas=100)
    comp = MockComponent(sub, 100)
    mix = MockMixture(PhysicalState.LIQUID, [comp])
    
    results, log = calculate_mixture_ate(mix)
    assert results['inhalation_gases'] is None

def test_flammable_liquids_cat2():
    # Cat 2: FP < 23, BP > 35
    h, ghs, log = evaluate_flammable_liquids(flash_point=10.0, boiling_point=80.0)
    assert "H225" in h
    assert "GHS02" in ghs

def test_flammable_liquids_cat3():
    # Cat 3: FP 30
    h, ghs, log = evaluate_flammable_liquids(flash_point=30.0, boiling_point=None)
    assert "H226" in h

def test_flammable_liquids_none():
    # Not Class: FP 70
    h, ghs, log = evaluate_flammable_liquids(flash_point=70.0, boiling_point=None)
    assert len(h) == 0
