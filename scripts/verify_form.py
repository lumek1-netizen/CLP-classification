from app import create_app
from app.forms.mixture import MixtureForm
from werkzeug.datastructures import MultiDict

app = create_app()

def verify_form_validation():
    with app.test_request_context():
        print("--- Verifying MixtureForm Validation ---")

        # Case 1: Valid pH
        form_valid = MixtureForm(formdata=MultiDict({'name': 'Test Valid', 'ph': '7.0'}), meta={'csrf': False})
        if form_valid.validate():
            print("SUCCESS: Valid pH accepted.")
        else:
            print(f"FAILURE: Valid pH rejected. Errors: {form_valid.errors}")

        # Case 2: Invalid pH (High)
        form_high = MixtureForm(formdata=MultiDict({'name': 'Test High', 'ph': '15.0'}), meta={'csrf': False})
        if not form_high.validate():
            print(f"SUCCESS: High pH rejected. Errors: {form_high.errors}")
        else:
            print("FAILURE: High pH accepted.")

        # Case 3: Invalid pH (Low) - assuming we don't allow negative in form based on my implementation
        form_low = MixtureForm(formdata=MultiDict({'name': 'Test Low', 'ph': '-1.0'}), meta={'csrf': False})
        if not form_low.validate():
            print(f"SUCCESS: Low pH rejected. Errors: {form_low.errors}")
        else:
            print("FAILURE: Low pH accepted.")
            
        # Case 4: No pH (Optional)
        form_none = MixtureForm(formdata=MultiDict({'name': 'Test None', 'ph': ''}), meta={'csrf': False})
        if form_none.validate():
             print("SUCCESS: Empty pH accepted (Optional).")
        else:
             print(f"FAILURE: Empty pH rejected. Errors: {form_none.errors}")

if __name__ == "__main__":
    verify_form_validation()
