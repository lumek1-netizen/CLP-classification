import pytest
from app.constants.clp import PHYSICAL_H_PHRASES, HEALTH_H_PHRASES, SCL_HAZARD_TO_H_CODE, SCL_HAZARD_TO_GHS_CODE
from app.constants.p_phrases import P_PHRASES_TEXT, H_TO_P_MAP

def test_physical_phrases_existence():
    """Ověří existenci fyzikálních H-vět."""
    assert "H200" in PHYSICAL_H_PHRASES
    assert "Nestabilní výbušnina" in PHYSICAL_H_PHRASES["H200"]
    assert "H220" in PHYSICAL_H_PHRASES
    assert "H290" in PHYSICAL_H_PHRASES

def test_repro_variants_existence():
    """Ověří existenci variant H360/H361."""
    assert "H360F" in HEALTH_H_PHRASES
    assert "H360D" in HEALTH_H_PHRASES
    assert "H360FD" in HEALTH_H_PHRASES
    assert "H361d" in HEALTH_H_PHRASES

def test_p_phrases_existence():
    """Ověří existenci nových P-vět."""
    assert "P370" in P_PHRASES_TEXT
    assert "P372" in P_PHRASES_TEXT
    assert "P401" in P_PHRASES_TEXT

def test_h_to_p_mapping():
    """Ověří mapování H->P pro nové věty."""
    # Fyzikální
    assert "H200" in H_TO_P_MAP
    assert "P370+P372+P380+P373" in H_TO_P_MAP["H200"]
    
    # Repro
    assert "H360F" in H_TO_P_MAP
    p_phrases = H_TO_P_MAP["H360F"]
    assert "P201" in p_phrases
    assert "P308+P313" in p_phrases

def test_scl_mappings():
    """Ověří aktualizaci SCL mapování."""
    assert "Unst. Expl" in SCL_HAZARD_TO_H_CODE
    assert SCL_HAZARD_TO_H_CODE["Unst. Expl"] == "H200"
    assert SCL_HAZARD_TO_GHS_CODE["Unst. Expl"] == "GHS01"
