from app.extensions import db

class MixtureComponent(db.Model):
    __tablename__ = 'mixture_component'
    id = db.Column(db.Integer, primary_key=True)
    mixture_id = db.Column(db.Integer, db.ForeignKey('mixture.id'), nullable=False)
    substance_id = db.Column(db.Integer, db.ForeignKey('substance.id'), nullable=False)
    concentration = db.Column(db.Float, nullable=False)
    
    mixture = db.relationship('Mixture', back_populates='components')
    substance = db.relationship('Substance', back_populates='components')

    __table_args__ = (db.UniqueConstraint('mixture_id', 'substance_id', name='_mixture_substance_uc'),)

    def to_dict(self):
        return {
            'substance_name': self.substance.name if self.substance else "Unknown",
            'concentration': self.concentration
        }
