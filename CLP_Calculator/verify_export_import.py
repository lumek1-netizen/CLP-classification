import os
import json
from app import create_app
from app.extensions import db
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification

app = create_app()

def verify():
    with app.app_context():
        print("Checking data...")
        substances = Substance.query.all()
        mixtures = Mixture.query.all()
        
        print(f"Substances found: {len(substances)}")
        print(f"Mixtures found: {len(mixtures)}")
        
        # Test Export logic
        data = {
            'substances': [s.to_dict() for s in substances],
            'mixtures': [m.to_dict() for m in mixtures]
        }
        
        export_json = json.dumps(data, indent=2)
        print("Export JSON created successfully.")
        
        # Test Import logic (simulation)
        imported_data = json.loads(export_json)
        print("Import JSON parsed successfully.")
        
        sub_names = [s['name'] for s in imported_data['substances']]
        mix_names = [m['name'] for m in imported_data['mixtures']]
        
        print(f"Names of substances in export: {sub_names[:5]}...")
        print(f"Names of mixtures in export: {mix_names[:5]}...")

        # Test component structure
        if imported_data['mixtures']:
            mix = imported_data['mixtures'][0]
            print(f"First mixture '{mix['name']}' has {len(mix['components'])} components.")
            for comp in mix['components']:
                print(f"  - Component: {comp['substance_name']}, Concentration: {comp['concentration']}%")

if __name__ == "__main__":
    verify()
