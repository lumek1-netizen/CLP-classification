import pytest
from app.models import Mixture, Substance, MixtureComponent, ComponentType
from app.services.clp.health import classify_by_concentration_limits

class MockSubstance:
    def __init__(self, name, health_h_phrases=None, scl_limits=None, ed_hh_cat=None, env_h_phrases=None):
        self.id = 1
        self.name = name
        self.health_h_phrases = health_h_phrases
        self.scl_limits = scl_limits
        self.ed_hh_cat = ed_hh_cat
        # Mock other needed attributes with defaults
        self.lc50_fish_96h = None
        self.ec50_daphnia_48h = None
        self.ec50_algae_72h = None
        self.noec_chronic = None
        self.env_h_phrases = env_h_phrases
        self.m_factor_acute = None
        self.m_factor_chronic = None
        self.ed_env_cat = None # Also needed for env
        self.is_pbt = False
        self.is_vpvb = False
        self.is_pmt = False
        self.is_vpvm = False

class MockComponent:
    def __init__(self, substance, concentration):
        self.substance = substance
        self.concentration = concentration
        self.component_type = ComponentType.SUBSTANCE

class MockMixture:
    def __init__(self, ph=None):
        self.ph = ph
        self.components = []
        self.classification_log = []
        self.health_hazards = set() # Add this if needed by the classifier (though usually it returns it)

    def to_dict(self):
        return {}

def test_skin_irritation_log():
    # Arrange
    # Skin Irrit 2 is triggered if sum >= 10%
    # We use a substance with H315 (Skin Irrit 2) at 15%
    sub = MockSubstance("Irritant", health_h_phrases="H315")
    comp = MockComponent(sub, 15.0)
    mix = MockMixture()
    mix.components = [comp]

    # Act
    hazards, ghs, log = classify_by_concentration_limits(mix)

    # Assert
    assert "H315" in hazards
    # Look for log entry regarding Skin Irrit 2
    log_texts = [entry['detail'] for entry in log]
    # We expect something like "Skin Irrit. 2: Sum = 15.0 >= 10.0" (exact wording depends on implementation)
    found = any("Skin Irrit. 2" in text and "15.0" in text for text in log_texts) \
            or any(entry['result'] == "H315" for entry in log) # Check result column too
    
    # Check specifically for contributor detail if possible, but at least the calculation step
    assert any("Skin Irrit. 2" in entry['step'] for entry in log), "Missing log step for Skin Irrit. 2"

def test_stot_se3_log():
    # Arrange
    # STOT SE 3 (H335) >= 20%
    sub = MockSubstance("Breathing Irritant", health_h_phrases="H335")
    comp = MockComponent(sub, 25.0)
    mix = MockMixture()
    mix.components = [comp]

    # Act
    hazards, ghs, log = classify_by_concentration_limits(mix)

    # Assert
    assert "H335" in hazards
    assert any("STOT SE 3" in entry['step'] for entry in log), "Missing log step for STOT SE 3"
    
def test_cmr_log():
    # Arrange
    # Carc 1A (H350) >= 0.1%
    sub = MockSubstance("Carcinogen", health_h_phrases="H350")
    comp = MockComponent(sub, 0.5)
    mix = MockMixture()
    mix.components = [comp]
    
    # Act
    hazards, ghs, log = classify_by_concentration_limits(mix)
    
    # Assert
    assert "H350" in hazards
    # Should log the contributor
    assert any("H350" in entry['result'] for entry in log)
    assert any("Carcinogen" in entry['detail'] for entry in log)

def test_negative_skin_log():
    # Arrange
    # Skin Corr 1A (H314) at 2.25% (Limit 5% for GCL, or specific SCL)
    # Generic limit for Skin Corr 1 is 5%.
    sub = MockSubstance("Weak Acid", health_h_phrases="H314")
    comp = MockComponent(sub, 2.25)
    mix = MockMixture()
    mix.components = [comp]
    
    # Act
    hazards, ghs, log = classify_by_concentration_limits(mix)
    
    # Assert
    assert "H314" not in hazards
    # Expect log entry saying why NOT classified
    # Look for "Skin Corr. 1" and "<" in detail, or "Neklasifikováno" in result
    log_texts = [entry['detail'] for entry in log]
    assert any("Skin Corr. 1" in entry['step'] for entry in log)
    assert any("Neklasifikováno" in entry['result'] for entry in log if "Skin Corr. 1" in entry['step'])

def test_env_skip_h_phrases_log():
    # Arrange
    # Substance with both H-phrases (e.g., H400) and experimental data (LC50)
    # The system should skip H-phrases and use LC50.
    from app.services.clp.env import classify_environmental_hazards
    
    sub = MockSubstance("Toxic Fish Food", env_h_phrases="H400") # Should be skipped
    sub.lc50_fish_96h = 0.5 # Toxic, Cat 1
    # Note: MockSubstance needs to have these attributes initialized in __init__ for clean testing
    # If not, we set them here on the instance.
    
    comp = MockComponent(sub, 30.0)
    mix = MockMixture()
    mix.components = [comp]
    
    # Act
    hazards, ghs, log = classify_environmental_hazards(mix)
    
    # Assert
    # 1. Check classification (Cat 1 because LC50 < 1mg/l and Conc > 2.5% [M=1])
    assert "H400" in hazards
    
    # 2. Check for Skip H-phrases log with specific data details
    skip_entries = [e for e in log if "Skip H-phrases" in e['step']]
    assert len(skip_entries) > 0, "Missing 'Skip H-phrases' log entry"
    
    detail = skip_entries[0]['detail']
    assert "Toxic Fish Food" in detail
    assert "LC50(fish)=0.5" in detail
    assert "Priorita testů" in detail

