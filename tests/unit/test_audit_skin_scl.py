
import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp.health import classify_by_concentration_limits

def test_audit_skin_corrosion_additivity_mixed_scls(app):
    """
    AUDIT TEST: Skin Corrosion Additivity with Mixed SCLs
    
    Reference: ECHA Guidance on the Application of the CLP Criteria, Section 3.2.3.3.4.2
    
    Guidance Example Logic:
    Sum(Conc_i / SCL_i) >= 1
    
    Scenario:
    - Substance A: Skin Corr 1B. SCL = 1.0% (More potent). Conc = 0.6%.
      Contribution: 0.6 / 1.0 = 0.6
    - Substance B: Skin Corr 1B. SCL = 5.0% (Standard). Conc = 1.0%.
      Contribution: 1.0 / 5.0 = 0.2
    - Substance C: Skin Corr 1A. SCL = 0.5% (Very potent). Conc = 0.1%.
      Contribution: 0.1 / 0.5 = 0.2
      
    Total Contribution: 0.6 + 0.2 + 0.2 = 1.0.
    Since Sum >= 1.0, the mixture MUST be classified as Skin Corr 1.
    """
    with app.app_context():
        # Setup substances
        sub_a = Substance(name="Sub A (SCL 1%)", health_h_phrases="H314", scl_limits="Skin Corr. 1B: >= 1.0")
        sub_b = Substance(name="Sub B (Standard 5%)", health_h_phrases="H314") # Implicit 5% GCL
        sub_c = Substance(name="Sub C (SCL 0.5%)", health_h_phrases="H314", scl_limits="Skin Corr. 1A: >= 0.5")
        
        mixture = Mixture(name="Audit Test Mixture")
        
        # Add components
        # Změna koncentrací tak, aby byly "Relevantní" (>= Cut-off/SCL)
        # SCL pro A je 1.0%. Conc musí být >= 1.0%.
        # SCL pro C je 0.5%. Conc musí být >= 0.5%.
        mixture.components = [
            MixtureComponent(substance=sub_a, concentration=1.0), # Relevant (1.0/1.0 = 1.0 contribution)
            MixtureComponent(substance=sub_b, concentration=1.0), # Relevant (1.0 >= 1% GCL) (1.0/5.0 = 0.2 contribution)
            MixtureComponent(substance=sub_c, concentration=0.5)  # Relevant (0.5/0.5 = 1.0 contribution)
        ]
        
        # Execute classification
        hazards, ghs, logs = classify_by_concentration_limits(mixture)
        
        # Verify
        # Total contribution: 1.0 + 0.2 + 1.0 = 2.2 >= 1.0 (Limit)
        # Weighted % sum: 5.0 + 1.0 + 5.0 = 11.0% >= 5%

