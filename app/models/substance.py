"""
Model chemické látky (Substance).

Definuje strukturu dat pro látky, včetně klasifikačních dat (H-věty, ATE, ekotoxicita).
"""
from sqlalchemy.orm import validates
import re
from app.extensions import db


class Substance(db.Model):
    """
    Reprezentuje chemickou látku v databázi.
    Obsahuje informace o názvu, CAS čísle, nebezpečnosti (H-věty, GHS),
    ATE hodnotách a M-faktorech pro výpočet klasifikace směsí.
    """

    __tablename__ = "substance"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    cas_number = db.Column(db.String(20), nullable=True, index=True)
    ghs_codes = db.Column(db.String(100), nullable=True)  # Piktogramy
    health_h_phrases = db.Column(db.Text, nullable=True)
    env_h_phrases = db.Column(db.Text, nullable=True)
    physical_h_phrases = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Údaje pro Akutní toxicitu (ATE)
    ate_oral = db.Column(db.Float, nullable=True)
    ate_dermal = db.Column(db.Float, nullable=True)
    ate_inhalation_vapours = db.Column(db.Float, nullable=True)
    ate_inhalation_dusts_mists = db.Column(db.Float, nullable=True)
    ate_inhalation_gases = db.Column(db.Float, nullable=True)

    m_factor_acute = db.Column(db.Integer, default=1)
    m_factor_chronic = db.Column(db.Integer, default=1)
    scl_limits = db.Column(db.Text, nullable=True)
    molecular_weight = db.Column(db.Float, nullable=True)  # Pro přepočet mg/l <-> ppm u plynů

    # Ekotoxické parametry (pro klasifikaci dle CLP Příloha I, část 4.1)
    # Akutní toxicita pro vodní prostředí - standardní testy podle CLP
    lc50_fish_96h = db.Column(db.Float, nullable=True)  # LC50 ryby, 96h (mg/L)
    ec50_daphnia_48h = db.Column(db.Float, nullable=True)  # EC50 daphnie, 48h (mg/L)
    ec50_algae_72h = db.Column(db.Float, nullable=True)  # EC50 řasy, 72h (mg/L)
    
    # Chronická toxicita
    noec_chronic = db.Column(db.Float, nullable=True)  # NOEC (No Observed Effect Concentration) mg/L
    
    # Toxicita pro savcí (pro úplný datový set)
    ld50_oral_mammal = db.Column(db.Float, nullable=True)  # LD50 orální, savci (mg/kg)
    ld50_dermal_mammal = db.Column(db.Float, nullable=True)  # LD50 dermální, savci (mg/kg)
    lc50_inhalation_rat_4h = db.Column(db.Float, nullable=True)  # LC50 inhalace, potkani, 4h (mg/L)

    # Nové třídy nebezpečnosti (2026 / Nařízení 2023/707)
    ed_hh_cat = db.Column(db.Integer, nullable=True)  # Endokrinní disrupce - zdraví (1, 2)
    ed_env_cat = db.Column(db.Integer, nullable=True)  # Endokrinní disrupce - živ. prostř. (1, 2)
    is_pbt = db.Column(db.Boolean, default=False)
    is_vpvb = db.Column(db.Boolean, default=False)
    is_pmt = db.Column(db.Boolean, default=False)
    is_vpvm = db.Column(db.Boolean, default=False)
    is_svhc = db.Column(db.Boolean, default=False) # Substance of Very High Concern
    is_reach_annex_xiv = db.Column(db.Boolean, default=False) # REACH Příloha XIV
    is_reach_annex_xvii = db.Column(db.Boolean, default=False) # REACH Příloha XVII

    components = db.relationship(
        "MixtureComponent",
        back_populates="substance",
        lazy=True,
        # REMOVED: cascade="all, delete-orphan" -> This prevented safe deletion checks!
        # Now, if we try to delete Substance, DB ForeignKey constraint will block it
        # because MixtureComponents still exist.
    )

    __table_args__ = (
        db.CheckConstraint("ate_oral >= 0", name="check_ate_oral_positive"),
        db.CheckConstraint("ate_dermal >= 0", name="check_ate_dermal_positive"),
        db.CheckConstraint(
            "ate_inhalation_vapours >= 0", name="check_ate_vapours_positive"
        ),
        db.CheckConstraint(
            "ate_inhalation_dusts_mists >= 0", name="check_ate_dusts_positive"
        ),
        db.CheckConstraint(
            "ate_inhalation_gases >= 0", name="check_ate_gases_positive"
        ),
        db.CheckConstraint("m_factor_acute >= 1", name="check_m_acute_positive"),
        db.CheckConstraint("m_factor_chronic >= 1", name="check_m_chronic_positive"),
        # Ekotoxické parametry - validace nezáporných hodnot
        db.CheckConstraint("lc50_fish_96h >= 0 OR lc50_fish_96h IS NULL", name="check_lc50_fish_positive"),
        db.CheckConstraint("ec50_daphnia_48h >= 0 OR ec50_daphnia_48h IS NULL", name="check_ec50_daphnia_positive"),
        db.CheckConstraint("ec50_algae_72h >= 0 OR ec50_algae_72h IS NULL", name="check_ec50_algae_positive"),
        db.CheckConstraint("noec_chronic >= 0 OR noec_chronic IS NULL", name="check_noec_positive"),
        db.CheckConstraint("ld50_oral_mammal >= 0 OR ld50_oral_mammal IS NULL", name="check_ld50_oral_mammal_positive"),
        db.CheckConstraint("ld50_dermal_mammal >= 0 OR ld50_dermal_mammal IS NULL", name="check_ld50_dermal_mammal_positive"),
        db.CheckConstraint("lc50_inhalation_rat_4h >= 0 OR lc50_inhalation_rat_4h IS NULL", name="check_lc50_inhalation_rat_positive"),
    )

    @validates("cas_number")
    def validate_cas(self, key, value):
        if value and not re.match(r"^\d{2,7}-\d{2}-\d$", value):
            raise ValueError(f"Neplatný formát CAS: {value}")
        return value

    @validates(
        "ate_oral",
        "ate_dermal",
        "ate_inhalation_vapours",
        "ate_inhalation_dusts_mists",
        "ate_inhalation_gases",
        "lc50_fish_96h",
        "ec50_daphnia_48h",
        "ec50_algae_72h",
        "noec_chronic",
        "ld50_oral_mammal",
        "ld50_dermal_mammal",
        "lc50_inhalation_rat_4h",
    )
    def validate_ate(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} nesmí být záporné číslo")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "cas_number": self.cas_number,
            "ghs_codes": self.ghs_codes,
            "health_h_phrases": self.health_h_phrases,
            "env_h_phrases": self.env_h_phrases,
            "physical_h_phrases": self.physical_h_phrases,
            "ate_oral": self.ate_oral,
            "ate_dermal": self.ate_dermal,
            "ate_inhalation_vapours": self.ate_inhalation_vapours,
            "ate_inhalation_dusts_mists": self.ate_inhalation_dusts_mists,
            "ate_inhalation_gases": self.ate_inhalation_gases,
            "m_factor_acute": self.m_factor_acute,
            "m_factor_chronic": self.m_factor_chronic,
            "scl_limits": self.scl_limits,

            "ed_hh_cat": self.ed_hh_cat,
            "ed_env_cat": self.ed_env_cat,
            "is_pbt": self.is_pbt,
            "is_vpvb": self.is_vpvb,
            "is_pmt": self.is_pmt,
            "is_vpvm": self.is_vpvm,

            "is_svhc": self.is_svhc,
            "is_reach_annex_xiv": self.is_reach_annex_xiv,
            "is_reach_annex_xvii": self.is_reach_annex_xvii,
            # Ekotoxické parametry
            "lc50_fish_96h": self.lc50_fish_96h,
            "ec50_daphnia_48h": self.ec50_daphnia_48h,
            "ec50_algae_72h": self.ec50_algae_72h,
            "noec_chronic": self.noec_chronic,
            "ld50_oral_mammal": self.ld50_oral_mammal,
            "ld50_dermal_mammal": self.ld50_dermal_mammal,
            "lc50_inhalation_rat_4h": self.lc50_inhalation_rat_4h,
        }
