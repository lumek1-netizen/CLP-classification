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
    def __init__(self, physical_state, components):
        self.physical_state = physical_state
        self.components = components

def verify_liquid_dust_behavior():
    print("--- Verifying Liquid Dust/Mist Behavior ---")
    
    # Setup: Mixture is LIQUID
    # Component has only ATE for Dust/Mist (e.g. valid for a dissolved solid or a mist-forming liquid)
    sub = MockSubstance("DustySub", ate_dust=1.5) # Cat 4 range
    comp = MockComponent(sub, 100) # 100% concentration
    
    mix = MockMixture(PhysicalState.LIQUID, [comp])
    
    results, log = calculate_mixture_ate(mix)
    
    ate_dust_mist = results.get('inhalation_dusts_mists')
    
    print(f"Physical State: {mix.physical_state}")
    print(f"Component ATE (Dust/Mist): {sub.ate_inhalation_dusts_mists}")
    print(f"Calculated ATEmix (Dust/Mist): {ate_dust_mist}")
    
    if ate_dust_mist is not None:
        print("RESULT: ATE Dust/Mist IS calculated for Liquids.")
    else:
        print("RESULT: ATE Dust/Mist is NOT calculated for Liquids.")

if __name__ == "__main__":
    verify_liquid_dust_behavior()
