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

    # Nové třídy nebezpečnosti (2026 / Nařízení 2023/707)
    is_lact = db.Column(db.Boolean, default=False)  # H362: Účinky na laktaci
    ed_hh_cat = db.Column(db.Integer, nullable=True)  # Endokrinní disrupce - zdraví (1, 2)
    ed_env_cat = db.Column(db.Integer, nullable=True)  # Endokrinní disrupce - živ. prostř. (1, 2)
    is_pbt = db.Column(db.Boolean, default=False)
    is_vpvb = db.Column(db.Boolean, default=False)
    is_pmt = db.Column(db.Boolean, default=False)
    is_vpvm = db.Column(db.Boolean, default=False)
    has_ozone = db.Column(db.Boolean, default=False) # H420
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
            "ate_oral": self.ate_oral,
            "ate_dermal": self.ate_dermal,
            "ate_inhalation_vapours": self.ate_inhalation_vapours,
            "ate_inhalation_dusts_mists": self.ate_inhalation_dusts_mists,
            "ate_inhalation_gases": self.ate_inhalation_gases,
            "m_factor_acute": self.m_factor_acute,
            "m_factor_chronic": self.m_factor_chronic,
            "scl_limits": self.scl_limits,
            "is_lact": self.is_lact,
            "ed_hh_cat": self.ed_hh_cat,
            "ed_env_cat": self.ed_env_cat,
            "is_pbt": self.is_pbt,
            "is_vpvb": self.is_vpvb,
            "is_pmt": self.is_pmt,
            "is_vpvm": self.is_vpvm,
            "has_ozone": self.has_ozone,
            "is_svhc": self.is_svhc,
            "is_reach_annex_xiv": self.is_reach_annex_xiv,
            "is_reach_annex_xvii": self.is_reach_annex_xvii,
        }
