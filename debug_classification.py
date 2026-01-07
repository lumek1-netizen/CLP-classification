from app import create_app
from app.extensions import db
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
import json

app = create_app()
app.config.update({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})

with app.app_context():
    db.create_all()
    s1 = Substance(name="Toxic Substance", ate_oral=100, health_h_phrases="H301,H315")
    db.session.add(s1)
    db.session.commit()
    
    mix = Mixture(name="Debug Mix")
    db.session.add(mix)
    db.session.flush()
    comp = MixtureComponent(mixture_id=mix.id, substance_id=s1.id, concentration=100)
    db.session.add(comp)
    db.session.commit()
    
    run_clp_classification(mix)
    db.session.commit()
    
    retrieved = Mixture.query.get(mix.id)
    print(f"Final Health Hazards: '{retrieved.final_health_hazards}'")
    print(f"Final GHS Codes: '{retrieved.final_ghs_codes}'")
    # print(f"Log: {retrieved.classification_log}")
