from app import create_app, db
from app.models import Mixture, Substance, MixtureComponent
from app.services.clp.engine import run_clp_classification

app = create_app()

def verify_features():
    with app.app_context():
        print("--- Verifying Extreme pH Logic ---")
        # 1. Test Low pH
        mixture_acid = Mixture.query.filter_by(name="Test Acidic Mixture").first()
        if mixture_acid:
            db.session.delete(mixture_acid)
            db.session.commit()

        mixture_acid = Mixture(name="Test Acidic Mixture", ph=1.0)
        # Add a dummy component to avoid empty check errors if any
        sub_water = Substance.query.filter_by(name="Water").first()
        if not sub_water:
            sub_water = Substance(name="Water", cas_number="7732-18-5")
            db.session.add(sub_water)
            db.session.commit()
            
        comp = MixtureComponent(substance=sub_water, concentration=100)
        mixture_acid.components.append(comp)
        db.session.add(mixture_acid)
        db.session.commit()
        
        run_clp_classification(mixture_acid)
        
        print(f"Mixture pH: {mixture_acid.ph}")
        print(f"Health Hazards: {mixture_acid.final_health_hazards}")
        if "H314" in (mixture_acid.final_health_hazards or ""):
            print("SUCCESS: Low pH triggered H314.")
        else:
            print("FAILURE: Low pH did NOT trigger H314.")

        # 2. Test High pH
        mixture_base = Mixture.query.filter_by(name="Test Basic Mixture").first()
        if mixture_base:
            db.session.delete(mixture_base)
            db.session.commit()
            
        mixture_base = Mixture(name="Test Basic Mixture", ph=13.0)
        mixture_base.components.append(MixtureComponent(substance=sub_water, concentration=100))
        db.session.add(mixture_base)
        db.session.commit()
        run_clp_classification(mixture_base)
        print(f"Mixture pH: {mixture_base.ph}")
        print(f"Health Hazards: {mixture_base.final_health_hazards}")
        if "H314" in (mixture_base.final_health_hazards or ""):
             print("SUCCESS: High pH triggered H314.")
        else:
             print("FAILURE: High pH did NOT trigger H314.")

        print("\n--- Verifying Unknown Env Toxicity Logic ---")
        # 3. Test Unknown Env Component
        # Create a substance with NO env hazards
        sub_unknown = Substance.query.filter_by(name="Unknown Stuff").first()
        if not sub_unknown:
            sub_unknown = Substance(name="Unknown Stuff", cas_number="000-00-0")
            # Ensure it has NO env phrases
            sub_unknown.env_h_phrases = None
            db.session.add(sub_unknown)
            db.session.commit()
        else:
            # Ensure it has NO env phrases
             sub_unknown.env_h_phrases = None
             db.session.commit()

        mixture_unknown = Mixture.query.filter_by(name="Test Unknown Env").first()
        if mixture_unknown:
            db.session.delete(mixture_unknown)
            db.session.commit()

        mixture_unknown = Mixture(name="Test Unknown Env")
        # 50% unknown, 50% water (also unknown actually in this test context if water has no env data)
        # But let's rely on the one we just created.
        mixture_unknown.components.append(MixtureComponent(substance=sub_unknown, concentration=50.0))
        db.session.add(mixture_unknown)
        db.session.commit()
        
        run_clp_classification(mixture_unknown)
        
        print(f"Unknown Env %: {mixture_unknown.unknown_env_toxicity_percent}")
        
        # We expect 50.0 if water is treated as known (unlikely unless configured) or 100.0 if water is also unknown.
        # Let's check the log
        log_detail = next((entry for entry in mixture_unknown.classification_log if entry.get("step") == "Neznámá toxicita (Env)"), None)
        if log_detail:
             print(f"Log found: {log_detail['detail']}")
             print("SUCCESS: Unknown toxicity detected.")
        else:
             print("FAILURE: Unknown toxicity NOT detected in log.")
             print(mixture_unknown.classification_log)

        # Cleanup
        db.session.delete(mixture_acid)
        db.session.delete(mixture_base)
        db.session.delete(mixture_unknown)
        db.session.delete(sub_unknown)
        # Keep water if it existed before, but we added it if missing. Ideally rollback but this is a test script.
        db.session.commit()

if __name__ == "__main__":
    verify_features()
