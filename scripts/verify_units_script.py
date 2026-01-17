
import sys
import os
import random
from app import create_app
from app.extensions import db
from app.models import Substance, Mixture

def check_units():
    app = create_app()
    with app.app_context():
        print("--- PHASE 1: Unit & Data Consistency Audit ---")
        
        # 1. Check Substances for Suspicious ATE Gas values
        # Gas limits: Cat 1 <= 100 ppm, Cat 2 <= 500 ppm.
        # If someone entered mg/l (e.g. 0.5 mg/l), it would look like 0.5 ppm which is EXTREMELY toxic.
        # Any gas ATE < 10 ppm is very suspicious unless it's a known chemical warfare agent.
        
        substances = Substance.query.all()
        suspicious_gases = []
        
        print(f"Scanning {len(substances)} substances...")
        
        for sub in substances:
            if sub.ate_inhalation_gases is not None and sub.ate_inhalation_gases > 0:
                val = sub.ate_inhalation_gases
                if val < 50:
                    suspicious_gases.append(f"{sub.name}: {val} (Possible mg/l entered as ppm?)")

        if suspicious_gases:
            print("\n[WARNING] Suspicious Gas ATE values (Input < 50):")
            for msg in suspicious_gases:
                print(f"  - {msg}")
        else:
            print("\n[OK] No obviously suspicious Gas ATE values found (< 50).")

        # 2. Check for ATE Unit Confusion (Oral/Dermal)
        # Oral/Dermal are mg/kg.
        # If someone entered values intended for air (e.g. 0.05 mg/l), it would be < 1 mg/kg.
        suspicious_oral = []
        for sub in substances:
            if sub.ate_oral is not None and sub.ate_oral > 0:
                 if sub.ate_oral < 1.0:
                     suspicious_oral.append(f"{sub.name}: {sub.ate_oral}")
        
        if suspicious_oral:
             print("\n[WARNING] Suspicious Oral ATE values (< 1 mg/kg):")
             for msg in suspicious_oral:
                 print(f"  - {msg}")
        else:
             print("\n[OK] No suspicious Oral ATE values (< 1 mg/kg).")

        # 3. Mixture Consistency Check
        # Grab 10 random mixtures and check component consistency
        mixtures = Mixture.query.all()
        sample_size = min(10, len(mixtures))
        sample_mixtures = random.sample(mixtures, sample_size) if mixtures else []

        print(f"\n[INFO] Auditing {len(sample_mixtures)} random mixtures for data integrity...")
        
        for mix in sample_mixtures:
            print(f"\nMixture: {mix.name} (ID: {mix.id})")
            print(f"  Physical State: {mix.physical_state}")
            
            # Check if physical state matches available ATEs of components
            # e.g. if Gas mixture has components with only Oral ATEs, that's weird (but not impossible if calculating Acute Tox unknown)
            
            has_relevant_data = False
            for comp in mix.components:
                sub = comp.substance
                conc = comp.concentration
                print(f"    - {sub.name} ({conc}%)")
                
                if mix.physical_state and str(mix.physical_state.value) == 'gas':
                    if sub.ate_inhalation_gases:
                        print(f"      -> Gas ATE: {sub.ate_inhalation_gases}")
                        has_relevant_data = True
                    elif sub.ate_inhalation_vapours or sub.ate_inhalation_dusts_mists:
                        print(f"      -> [WARN] Gas mixture contains component with Vapour/Mist data but no Gas data.")
                
                # Check for sum > 100% just in case
            
            total_conc = sum(c.concentration for c in mix.components)
            if total_conc > 100.000001: # float tol
                print(f"  [CRITICAL] Total concentration > 100%: {total_conc}")
            elif total_conc < 0:
                 print(f"  [CRITICAL] Negative concentration sum!")
            else:
                print(f"  Concentration Sum: {total_conc:.2f}%")

if __name__ == "__main__":
    check_units()
