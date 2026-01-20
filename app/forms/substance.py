from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, HiddenField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


def empty_to_none(value):
    """Převede prázdné stringy na None pro správnou validaci Optional polí."""
    if value == '' or value is None:
        return None
    return value


class SubstanceForm(FlaskForm):
    name = StringField("Název látky", validators=[DataRequired(), Length(max=100)])
    cas_number = StringField("CAS číslo", validators=[Optional(), Length(max=20)])
    ghs_codes = StringField(
        "GHS kódy (např. GHS05, GHS07)", validators=[Optional(), Length(max=100)]
    )

    # H-věty jsou zpracovávány přímo z request.form v route
    scl_limits = HiddenField()  # JSON nebo řetězec se SCL limity

    ate_oral = FloatField(
        "ATE orální (mg/kg)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    ate_dermal = FloatField(
        "ATE dermální (mg/kg)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    ate_inhalation_vapours = FloatField(
        "ATE inhalační - páry (mg/l)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    ate_inhalation_dusts_mists = FloatField(
        "ATE inhalační - prach/mlha (mg/l)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    ate_inhalation_gases = FloatField(
        "ATE inhalační - plyny (ppm)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    molecular_weight = FloatField(
        "Molekulová hmotnost (g/mol)", validators=[Optional(), NumberRange(min=0.01)], filters=[empty_to_none]
    )

    m_factor_acute = IntegerField(
        "M-faktor akutní", validators=[Optional(), NumberRange(min=1)], default=1, filters=[empty_to_none]
    )
    m_factor_chronic = IntegerField(
        "M-faktor chronický", validators=[Optional(), NumberRange(min=1)], default=1, filters=[empty_to_none]
    )

    # Ekotoxické parametry (CLP Příloha I, část 4.1)
    # Akutní toxicita pro vodní prostředí - standardní testy
    lc50_fish_96h = FloatField(
        "LC50 ryby, 96h (mg/L)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    ec50_daphnia_48h = FloatField(
        "EC50 daphnie, 48h (mg/L)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    ec50_algae_72h = FloatField(
        "EC50 řasy, 72h (mg/L)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    
    # Chronická toxicita
    noec_chronic = FloatField(
        "NOEC (mg/L)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    
    # Toxicita pro savce
    ld50_oral_mammal = FloatField(
        "LD50 orální, savci (mg/kg)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    ld50_dermal_mammal = FloatField(
        "LD50 dermální, savci (mg/kg)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )
    lc50_inhalation_rat_4h = FloatField(
        "LC50 inhalace, potkani, 4h (mg/L)", validators=[Optional(), NumberRange(min=0)], filters=[empty_to_none]
    )


    # Rozšíření 2026
    ed_hh_cat = SelectField("ED HH (Lidské zdraví)", choices=[(0, "Není"), (1, "ED HH 1"), (2, "ED HH 2")], coerce=int)
    ed_env_cat = SelectField("ED ENV (Živ. prostředí)", choices=[(0, "Není"), (1, "ED ENV 1"), (2, "ED ENV 2")], coerce=int)
    is_pbt = BooleanField("PBT (Perzistentní, biokumulativní, toxická)")
    is_vpvb = BooleanField("vPvB (Vysoce perzistentní, vysoce bioakumulativní)")
    is_pmt = BooleanField("PMT (Perzistentní, mobilní, toxická)")
    is_vpvm = BooleanField("vPvM (Vysoce perzistentní, vysoce mobilní)")
    is_svhc = BooleanField("Je SVHC (Látka vzbuzující mimořádné obavy)")
    is_reach_annex_xiv = BooleanField("REACH Příloha XIV (Povolování)")
    is_reach_annex_xvii = BooleanField("REACH Příloha XVII (Omezení)")

