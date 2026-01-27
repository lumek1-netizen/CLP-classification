import pytest
from app.forms.substance import SubstanceForm
from app.forms.mixture import MixtureForm
from app import create_app
from werkzeug.datastructures import MultiDict

@pytest.fixture
def app():
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    return app

def test_flexible_float_field_substance(app):
    with app.app_context():
        # Test with dot
        form = SubstanceForm(formdata=MultiDict({'name': 'Test', 'molecular_weight': '44.01'}))
        form.validate()
        assert form.molecular_weight.data == 44.01

        # Test with comma
        form = SubstanceForm(formdata=MultiDict({'name': 'Test', 'molecular_weight': '44,01'}))
        form.validate()
        assert form.molecular_weight.data == 44.01

def test_flexible_float_field_mixture(app):
    with app.app_context():
        # Test with dot
        form = MixtureForm(formdata=MultiDict({
            'name': 'Test Mix', 
            'ph': '7.5', 
            'physical_state': 'liquid', 
            'user_type': 'professional'
        }))
        form.validate()
        assert form.ph.data == 7.5

        # Test with comma
        form = MixtureForm(formdata=MultiDict({
            'name': 'Test Mix', 
            'ph': '7,5', 
            'physical_state': 'liquid', 
            'user_type': 'professional'
        }))
        form.validate()
        assert form.ph.data == 7.5
