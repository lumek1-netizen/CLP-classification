import pytest
from app.services.echa_service import ECHAService

def test_parse_scl_value_simple():
    service = ECHAService()
    assert service._parse_scl_value("C ≥ 15 %") == ">= 15"
    assert service._parse_scl_value("C > 5%") == "> 5"
    assert service._parse_scl_value("C ≤ 10 %") == "<= 10"

def test_parse_scl_value_range():
    service = ECHAService()
    # 5 ≤ C < 15  => C >= 5 AND C < 15
    assert service._parse_scl_value("5 % ≤ C < 15 %") == ">= 5; < 15"
    assert service._parse_scl_value("0,1 % ≤ C < 1 %") == ">= 0.1; < 1"

def test_parse_scl_value_complex():
    service = ECHAService()
    assert service._parse_scl_value("C ≥ 0.001 %") == ">= 0.001"

def test_parse_response_obligations():
    service = ECHAService()
    detail = {"substanceName": "Test", "casNumber": "1-2-3"}
    harmonised = {}
    obligations = [
        {"listName": "Candidate list of substances of very high concern (SVHC) for authorisation"},
        {"listName": "REACH Annex XIV"}
    ]
    
    res = service._parse_response(detail, harmonised, obligations)
    assert res["is_svhc"] is True
    assert res["is_reach_annex_xiv"] is True
    assert res["is_reach_annex_xvii"] is False

def test_parse_response_scl():
    service = ECHAService()
    detail = {"substanceName": "Sulfuric", "casNumber": "7664-93-9"}
    harmonised = {
        "concentrationLimits": [
            {"hazardClass": "Skin Corr. 1A", "concentrationLimitValue": "C ≥ 15 %"},
            {"hazardClass": "Skin Irrit. 2", "concentrationLimitValue": "5 % ≤ C < 15 %"}
        ]
    }
    obligations = []
    
    res = service._parse_response(detail, harmonised, obligations)
    assert "Skin Corr. 1A: >= 15" in res["scl_limits"]
    assert "Skin Irrit. 2: >= 5; < 15" in res["scl_limits"]
