from app.extensions import db

class Substance(db.Model):
    __tablename__ = 'substance'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    cas_number = db.Column(db.String(20), nullable=True)
    ghs_codes = db.Column(db.String(100), nullable=True) # Piktogramy
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
    
    components = db.relationship('MixtureComponent', back_populates='substance', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cas_number': self.cas_number,
            'ghs_codes': self.ghs_codes,
            'health_h_phrases': self.health_h_phrases,
            'env_h_phrases': self.env_h_phrases,
            'ate_oral': self.ate_oral,
            'ate_dermal': self.ate_dermal,
            'ate_inhalation_vapours': self.ate_inhalation_vapours,
            'ate_inhalation_dusts_mists': self.ate_inhalation_dusts_mists,
            'ate_inhalation_gases': self.ate_inhalation_gases,
            'm_factor_acute': self.m_factor_acute,
            'm_factor_chronic': self.m_factor_chronic,
            'scl_limits': self.scl_limits
        }
