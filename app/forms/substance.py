from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, HiddenField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class SubstanceForm(FlaskForm):
    name = StringField("Název látky", validators=[DataRequired(), Length(max=100)])
    cas_number = StringField("CAS číslo", validators=[Optional(), Length(max=20)])
    ghs_codes = StringField(
        "GHS kódy (např. GHS05, GHS07)", validators=[Optional(), Length(max=100)]
    )

    # H-věty jsou zpracovávány přímo z request.form v route
    scl_limits = HiddenField()  # JSON nebo řetězec se SCL limity

    ate_oral = FloatField(
        "ATE orální (mg/kg)", validators=[Optional(), NumberRange(min=0)]
    )
    ate_dermal = FloatField(
        "ATE dermální (mg/kg)", validators=[Optional(), NumberRange(min=0)]
    )
    ate_inhalation_vapours = FloatField(
        "ATE inhalační - páry (mg/l)", validators=[Optional(), NumberRange(min=0)]
    )
    ate_inhalation_dusts_mists = FloatField(
        "ATE inhalační - prach/mlha (mg/l)", validators=[Optional(), NumberRange(min=0)]
    )
    ate_inhalation_gases = FloatField(
        "ATE inhalační - plyny (ppm)", validators=[Optional(), NumberRange(min=0)]
    )

    m_factor_acute = IntegerField(
        "M-faktor akutní", validators=[Optional(), NumberRange(min=1)], default=1
    )
    m_factor_chronic = IntegerField(
        "M-faktor chronický", validators=[Optional(), NumberRange(min=1)], default=1
    )


    # Rozšíření 2026
    is_lact = BooleanField("Účinky na laktaci (H362)")
    ed_hh_cat = SelectField("ED HH (Lidské zdraví)", choices=[(0, "Není"), (1, "ED HH 1"), (2, "ED HH 2")], coerce=int)
    ed_env_cat = SelectField("ED ENV (Živ. prostředí)", choices=[(0, "Není"), (1, "ED ENV 1"), (2, "ED ENV 2")], coerce=int)
    is_pbt = BooleanField("PBT (Perzistentní, biokumulativní, toxická)")
    is_vpvb = BooleanField("vPvB (Vysoce perzistentní, vysoce bioakumulativní)")
    is_pmt = BooleanField("PMT (Perzistentní, mobilní, toxická)")
    is_vpvm = BooleanField("vPvM (Vysoce perzistentní, vysoce mobilní)")
    has_ozone = BooleanField("Nebezpečná pro ozonovou vrstvu (H420)")
