"""
Debug script to check if SCL data is being saved to the database.
"""

import os
import sys
sys.path.append(os.getcwd())

from app import create_app
from app.models import Substance

app = create_app()

with app.app_context():
    # Check substance with ID 6 (the one user was editing)
    substance = Substance.query.get(6)
    
    if substance:
        print(f"=== Substance ID: 6 ===")
        print(f"Name: {substance.name}")
        print(f"CAS: {substance.cas_number}")
        print(f"SCL Limits (raw): {repr(substance.scl_limits)}")
        print()
        
        if substance.scl_limits:
            print("SCL data EXISTS in database!")
            print(f"Length: {len(substance.scl_limits)} characters")
            print(f"Content: {substance.scl_limits}")
        else:
            print("❌ SCL data is EMPTY/NULL in database!")
    else:
        print("❌ Substance with ID 6 NOT FOUND!")
