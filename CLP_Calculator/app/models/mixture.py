from app.extensions import db

class Mixture(db.Model):
    __tablename__ = 'mixture'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_date = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    final_health_hazards = db.Column(db.Text, nullable=True)
    final_environmental_hazards = db.Column(db.Text, nullable=True)
    final_ghs_codes = db.Column(db.String(100), nullable=True)
    
    final_atemix_oral = db.Column(db.Float, nullable=True)
    final_atemix_dermal = db.Column(db.Float, nullable=True)
    final_atemix_inhalation = db.Column(db.Float, nullable=True)
    
    final_signal_word = db.Column(db.String(50), nullable=True)
    classification_log = db.Column(db.JSON, nullable=True)
    
    components = db.relationship('MixtureComponent', back_populates='mixture', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'final_health_hazards': self.final_health_hazards,
            'final_environmental_hazards': self.final_environmental_hazards,
            'final_ghs_codes': self.final_ghs_codes,
            'final_atemix_oral': self.final_atemix_oral,
            'final_atemix_dermal': self.final_atemix_dermal,
            'final_atemix_inhalation': self.final_atemix_inhalation,
            'final_signal_word': self.final_signal_word,
            'components': [c.to_dict() for c in self.components]
        }
