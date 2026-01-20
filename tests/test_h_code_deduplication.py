
import pytest
from app import create_app, db
from app.models import Substance

class TestHCodeDeduplication:
    
    def setup_method(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def teardown_method(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_h362_in_health_h_phrases(self):
        """Test, že H362 lze uložit do health_h_phrases a atribut is_lact neexistuje."""
        substance = Substance(
            name="Test Lactation Substance",
            health_h_phrases="H300, H362",
            env_h_phrases="H400"
        )
        db.session.add(substance)
        db.session.commit()
        
        saved_substance = db.session.get(Substance, substance.id)
        assert "H362" in saved_substance.health_h_phrases
        assert not hasattr(saved_substance, 'is_lact')

    def test_h420_in_env_h_phrases(self):
        """Test, že H420 lze uložit do env_h_phrases a atribut has_ozone neexistuje."""
        substance = Substance(
            name="Test Ozone Substance",
            health_h_phrases="H300",
            env_h_phrases="H400, H420"
        )
        db.session.add(substance)
        db.session.commit()
        
        saved_substance = db.session.get(Substance, substance.id)
        assert "H420" in saved_substance.env_h_phrases
        assert not hasattr(saved_substance, 'has_ozone')
    
    def test_csv_export_does_not_contain_deprecated_fields(self):
        """Test, že exportní funkce již nepracuje s deprecated poli (nepřímo)."""
        # Tento test spíše ověřuje, že export nespadne
        from app.services.export_service import export_substances_to_csv
        
        substance = Substance(
            name="Export Test",
            health_h_phrases="H362",
            env_h_phrases="H420"
        )
        db.session.add(substance)
        db.session.commit()
        
        csv_output = export_substances_to_csv([substance.id])
        assert "is_lact" not in csv_output
        assert "has_ozone" not in csv_output
        assert "H362" in csv_output
        assert "H420" in csv_output
