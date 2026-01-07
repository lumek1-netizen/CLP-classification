import pytest
from app.models import Substance, User, Mixture, MixtureComponent
from app.extensions import db


def test_new_user(app):
    with app.app_context():
        user = User(username="newuser")
        user.set_password("flask")
        assert user.username == "newuser"
        assert user.check_password("flask")
        assert not user.check_password("python")


def test_substance_model(app):
    with app.app_context():
        substance = Substance(name="Acetone", cas_number="67-64-1", ate_oral=5800)
        db.session.add(substance)
        db.session.commit()

        retrieved = Substance.query.filter_by(name="Acetone").first()
        assert retrieved.id is not None
        assert retrieved.cas_number == "67-64-1"
        assert retrieved.ate_oral == 5800


def test_mixture_model(app, sample_substance):
    with app.app_context():
        # sample_substance fixture už látku vytvořila
        retrieved_sub = Substance.query.filter_by(name="Test Substance").first()

        mixture = Mixture(name="Test Mixture")
        db.session.add(mixture)
        db.session.commit()

        comp = MixtureComponent(
            mixture_id=mixture.id, substance_id=retrieved_sub.id, concentration=10.5
        )
        db.session.add(comp)
        db.session.commit()

        retrieved_mix = Mixture.query.filter_by(name="Test Mixture").first()
        assert len(retrieved_mix.components) == 1
        assert retrieved_mix.components[0].concentration == 10.5
        assert retrieved_mix.components[0].substance.name == "Test Substance"
