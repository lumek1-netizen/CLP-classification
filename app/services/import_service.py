# app/services/import_service.py
"""
Import service pro hromadné importování látek z CSV.
"""

from typing import Dict, List, Any
from app.extensions import db
from app.models import Substance
from app.services.csv_parser import parse_substances_csv
from app.services.validation import check_duplicate_cas
from app.constants.clp import HEALTH_H_PHRASES, ENV_H_PHRASES
from sqlalchemy.exc import IntegrityError


def import_substances_from_csv(file, user_id=None) -> Dict[str, Any]:
    """
    Importuje látky z CSV souboru.
    
    Args:
        file: Stream souboru (z objektu request.files)
        user_id: ID uživatele (pro účely auditního logu)
        
    Returns:
        {
            'total': int,           # Celkový počet řádků
            'success': int,         # Úspěšně importováno
            'skipped': int,         # Přeskočeno (duplicity)
            'errors': list,         # Seznam chyb
            'warnings': list        # Seznam varování
        }
    """
    result = {
        'total': 0,
        'success': 0,
        'skipped': 0,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Parsování CSV
        valid_h_phrases = set(HEALTH_H_PHRASES.keys())
        valid_env_phrases = set(ENV_H_PHRASES.keys())
        
        parsed_substances, parse_errors, parse_warnings = parse_substances_csv(
            file, 
            valid_h_phrases, 
            valid_env_phrases
        )
        
        result['errors'].extend(parse_errors)
        result['warnings'].extend(parse_warnings)
        result['total'] = len(parsed_substances)
        
        # Pokud jsou kritické chyby při parsování, zastavit
        if parse_errors:
            return result
        
        # Import látek
        for substance_data in parsed_substances:
            try:
                # Kontrola duplicitního CAS
                cas = substance_data.get('cas_number')
                if cas:
                    existing = check_duplicate_cas(cas)
                    if existing:
                        result['skipped'] += 1
                        result['warnings'].append(
                            f"Látka s CAS {cas} přeskočena - již existuje jako '{existing.name}'"
                        )
                        continue
                
                # Vytvoření nové látky
                new_substance = Substance(**substance_data)
                db.session.add(new_substance)
                
            except Exception as e:
                result['errors'].append(
                    f"Chyba při importu látky '{substance_data.get('name', 'N/A')}': {str(e)}"
                )
        
        # Commit všech změn najednou (bulk insert)
        try:
            db.session.commit()
            result['success'] = result['total'] - result['skipped'] - len([e for e in result['errors'] if 'Chyba při importu látky' in e])
        except IntegrityError as e:
            db.session.rollback()
            result['errors'].append(f"Chyba při ukládání do databáze: {str(e)}")
            result['success'] = 0
    
    except Exception as e:
        db.session.rollback()
        result['errors'].append(f"Neočekávaná chyba: {str(e)}")
    
    return result
