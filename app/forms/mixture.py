from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, BooleanField
from app.constants.clp import PhysicalState, UserType
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class MixtureForm(FlaskForm):
    name = StringField("Název směsi", validators=[DataRequired(), Length(max=100)])
    ph = FloatField(
        "pH (volitelné)",
        validators=[
            Optional(),
            NumberRange(min=0, max=14, message="Hodnota pH musí být v rozmezí 0 až 14."),
        ],
        description="Zadejte hodnotu pH (0-14). Extrémní hodnoty (≤2 nebo ≥11.5) automaticky klasifikují směs jako žíravou (Skin Corr. 1).",
    )
    physical_state = SelectField(
        "Fyzikální stav",
        choices=[(e.value, e.value) for e in PhysicalState],
        validators=[DataRequired()],
    )
    user_type = SelectField(
        "Typ použití",
        choices=[(e.value, e.value) for e in UserType],
        default=UserType.PROFESSIONAL.value,
        validators=[DataRequired()],
        description="Určuje, jaké P-věty se budou zobrazovat (např. spotřebitelské vs. průmyslové).",
    )
    flash_point = FloatField(
        "Bod vzplanutí (°C)",
        validators=[Optional()],
        description="Nutné pro klasifikaci hořlavosti kapalin.",
    )
    boiling_point = FloatField(
        "Bod varu (°C)",
        validators=[Optional()],
        description="Nutné pro klasifikaci hořlavosti kapalin v kombinaci s bodem vzplanutí.",
    )
    can_generate_mist = BooleanField(
        "Může vytvářet mlhu?",
        description="Zaškrtněte, pokud může směs tvořit aerosoly nebo mlhy (např. při sprejování). Pokud ne, inhalační toxicita prachu/mlhy se nebude počítat.",
        default=False,
    )
    # Komponenty se řeší dynamicky v request.form, ale CSRF token potřebujeme
