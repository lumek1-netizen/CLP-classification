
import pytest
from app.services.clp.p_phrases import assign_p_phrases

def test_assign_p_phrases_empty():
    """Test with empty H-phrases set."""
    h_phrases = set()
    p_phrases = assign_p_phrases(h_phrases)
    assert p_phrases == []

def test_assign_p_phrases_acute_tox_oral():
    """Test H300 (Acute Tox 1/2 Oral) - should result in specific P-phrases."""
    h_phrases = {"H300"}
    p_phrases = assign_p_phrases(h_phrases)
    
    expected = ["P264", "P270", "P301+P310", "P321", "P330", "P405", "P501"]
    assert sorted(p_phrases) == sorted(expected)

def test_assign_p_phrases_multiple_hazards():
    """Test combination of hazards (e.g. H300 + H314) and deduplication."""
    h_phrases = {"H300", "H314"}
    
    # H300 -> ["P264", "P270", "P301+P310", "P321", "P330", "P405", "P501"]
    # H314 -> ["P260", "P264", "P280", "P301+P330+P331", "P303+P361+P353", "P363", "P304+P340", "P310", "P321", "P305+P351+P338", "P405", "P501"]
    
    # Expected union:
    # P260, P264, P270, P280, P301+P310, P301+P330+P331, P303+P361+P353, P304+P340, P305+P351+P338, P310, P321, P330, P363, P405, P501
    
    p_phrases = assign_p_phrases(h_phrases)
    
    assert "P264" in p_phrases # Both
    assert "P501" in p_phrases # Both
    assert "P270" in p_phrases # H300
    assert "P280" in p_phrases # H314
    assert "P301+P310" in p_phrases # H300
    assert "P301+P330+P331" in p_phrases # H314
    
    # Check uniqueness count basics
    assert len(p_phrases) == len(set(p_phrases))

def test_assign_p_phrases_unknown_h_code():
    """Test handling of H-code that has no mapping."""
    h_phrases = {"H999"} # Non-existent
    p_phrases = assign_p_phrases(h_phrases)
    assert p_phrases == []
