import enum
from sqlalchemy.orm import validates
from app.extensions import db


class ComponentType(enum.Enum):
    """Typ komponenty ve směsi."""
    SUBSTANCE = "substance"
    MIXTURE = "mixture"


class MixtureComponent(db.Model):
    __tablename__ = "mixture_component"
    id = db.Column(db.Integer, primary_key=True)
    mixture_id = db.Column(db.Integer, db.ForeignKey("mixture.id"), nullable=False)
    
    # Typ komponenty (látka nebo směs)
    component_type = db.Column(
        db.Enum(ComponentType), 
        default=ComponentType.SUBSTANCE, 
        nullable=False
    )
    
    # Pro látky
    substance_id = db.Column(db.Integer, db.ForeignKey("substance.id"), nullable=True)
    
    # Pro směsi
    component_mixture_id = db.Column(db.Integer, db.ForeignKey("mixture.id"), nullable=True)
    
    concentration = db.Column(db.Float, nullable=False)

    mixture = db.relationship("Mixture", back_populates="components", foreign_keys=[mixture_id])
    substance = db.relationship("Substance", back_populates="components")
    component_mixture = db.relationship(
        "Mixture", 
        foreign_keys=[component_mixture_id],
        backref="used_in_mixtures"
    )

    __table_args__ = (
        db.CheckConstraint(
            "concentration > 0 AND concentration <= 100",
            name="check_concentration_range",
        ),
    )

    @validates("concentration")
    def validate_concentration(self, key, value):
        if value is None or value <= 0 or value > 100:
            raise ValueError(
                f"Koncentrace musí být v rozsahu (0, 100], získáno: {value}"
            )
        return value

    @validates("substance_id", "component_mixture_id", "component_type")
    def validate_consistency(self, key, value):
        # Tato validace se spustí při přiřazování hodnot.
        # Poznámka: Při prvotním vytváření objektu se vztahy (substance=...) 
        # nemusí okamžitě projevit v xxx_id polích.
        return value

    def check_consistency(self):
        """Manuální kontrola konzistence, kterou lze volat před save."""
        if self.component_type == ComponentType.SUBSTANCE:
            if not self.substance_id and not self.substance:
                return False, "Chybí látka pro typ 'substance'"
            if self.component_mixture_id or self.component_mixture:
                return False, "Směs nesmí být nastavena pro typ 'substance'"
        elif self.component_type == ComponentType.MIXTURE:
            if not self.component_mixture_id and not self.component_mixture:
                return False, "Chybí směs pro typ 'mixture'"
            if self.substance_id or self.substance:
                return False, "Látka nesmí být nastavena pro typ 'mixture'"
        return True, ""

    def get_component_name(self):
        """Vrátí název komponenty podle typu."""
        if self.component_type == ComponentType.SUBSTANCE:
            return self.substance.name if self.substance else "Unknown Substance"
        elif self.component_type == ComponentType.MIXTURE:
            return self.component_mixture.name if self.component_mixture else "Unknown Mixture"
        return "Unknown"

    def to_dict(self):
        return {
            "component_type": self.component_type.value if self.component_type else None,
            "substance_id": self.substance_id,
            "component_mixture_id": self.component_mixture_id,
            "substance_name": self.substance.name if self.substance else None,
            "mixture_name": self.component_mixture.name if self.component_mixture else None,
            "component_name": self.get_component_name(),
            "concentration": self.concentration,
        }

