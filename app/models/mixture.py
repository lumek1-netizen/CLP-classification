from app.extensions import db
from app.constants.clp import PhysicalState, UserType


class Mixture(db.Model):
    """
    Reprezentuje chemickou směs v databázi.
    Ukládá vypočtenou klasifikaci, GHS symboly, signální slovo a detailní log klasifikace.
    Propojena se složkami (Substance) skrze MixtureComponent.
    """

    __tablename__ = "mixture"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_date = db.Column(db.DateTime, default=db.func.now(), index=True)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    final_health_hazards = db.Column(db.Text, nullable=True)
    final_physical_hazards = db.Column(db.Text, nullable=True)
    final_environmental_hazards = db.Column(db.Text, nullable=True)
    final_ghs_codes = db.Column(db.String(100), nullable=True)
    final_precautionary_statements = db.Column(db.Text, nullable=True)

    final_atemix_oral = db.Column(db.Float, nullable=True)
    final_atemix_dermal = db.Column(db.Float, nullable=True)
    final_atemix_inhalation = db.Column(db.Float, nullable=True)

    final_signal_word = db.Column(db.String(50), nullable=True)
    classification_log = db.Column(db.JSON, nullable=True)
    
    # New fields for CLP improvements
    ph = db.Column(db.Float, nullable=True)
    unknown_env_toxicity_percent = db.Column(db.Float, nullable=True)

    # Physical properties
    physical_state = db.Column(db.Enum(PhysicalState), default=PhysicalState.LIQUID, nullable=False)
    flash_point = db.Column(db.Float, nullable=True)
    boiling_point = db.Column(db.Float, nullable=True)
    can_generate_mist = db.Column(db.Boolean, default=False, nullable=False)
    
    # User type for P-phrase filtering
    user_type = db.Column(db.Enum(UserType), default=UserType.PROFESSIONAL, nullable=True)

    components = db.relationship(
        "MixtureComponent",
        back_populates="mixture",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "final_health_hazards": self.final_health_hazards,
            "final_environmental_hazards": self.final_environmental_hazards,
            "final_ghs_codes": self.final_ghs_codes,
            "final_precautionary_statements": self.final_precautionary_statements,
            "final_atemix_oral": self.final_atemix_oral,
            "final_atemix_dermal": self.final_atemix_dermal,
            "final_atemix_inhalation": self.final_atemix_inhalation,
            "final_signal_word": self.final_signal_word,
            "ph": self.ph,
            "unknown_env_toxicity_percent": self.unknown_env_toxicity_percent,
            "user_type": self.user_type.value if self.user_type else None,
            "physical_state": self.physical_state.value if self.physical_state else None,
            "flash_point": self.flash_point,
            "boiling_point": self.boiling_point,
            "can_generate_mist": self.can_generate_mist,
            "components": [c.to_dict() for c in self.components],
        }
