
from app.services.clp.ate import _determine_ate_category
from app.constants.clp import ATE_LIMITS

def verify_ate_limits():
    print("Verifying ATE Limits...")
    
    # Check Oral
    print(f"Oral Limits: {ATE_LIMITS['oral']}")
    assert len(ATE_LIMITS['oral']) == 4, "Oral limits should have 4 categories"
    assert ATE_LIMITS['oral'][-1] == 2000, "Oral max limit should be 2000"
    
    # Check classification logic
    # Cat 4
    cat = _determine_ate_category(2000, 'oral')
    print(f"Value 2000 -> Cat {cat}")
    assert cat == 4, "2000 should be Cat 4"
    
    # Over Cat 4 (should be 5 -> Not Classified)
    cat = _determine_ate_category(2001, 'oral')
    print(f"Value 2001 -> Cat {cat}")
    assert cat == 5, "2001 should be Cat 5 (Internal for Not Classified)"
    
    # Previous Cat 5 range
    cat = _determine_ate_category(3000, 'oral')
    print(f"Value 3000 -> Cat {cat}")
    assert cat == 5, "3000 should be Cat 5 (Internal for Not Classified)"
    
    cat = _determine_ate_category(5000, 'oral')
    print(f"Value 5000 -> Cat {cat}")
    assert cat == 5, "5000 should be Cat 5 (Internal for Not Classified)"

    print("ALL CHECKS PASSED")

if __name__ == "__main__":
    verify_ate_limits()
