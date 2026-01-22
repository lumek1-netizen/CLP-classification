"""
Testy pro podporu směsí jako komponent.

Testuje:
- Vytvoření směsi s látkou
- Vytvoření směsi se směsí
- Detekci cyklické závislosti
- Rozbalení směsí na látky
- Přepočet koncentrací
"""

import pytest
from app import create_app, db
from app.models import Mixture, Substance, MixtureComponent, ComponentType
from app.services.mixture_service import MixtureService


@pytest.fixture
def app():
    """Vytvoří testovací aplikaci."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Vytvoří testovacího klienta."""
    return app.test_client()


def test_create_mixture_with_substance(app):
    """Test vytvoření směsi s látkou."""
    with app.app_context():
        # Vytvořit látku
        substance = Substance(name="Ethanol", cas_number="64-17-5")
        db.session.add(substance)
        db.session.commit()
        
        # Vytvořit směs
        mixture = Mixture(name="Test Mixture")
        db.session.add(mixture)
        db.session.flush()
        
        # Přidat komponentu
        component = MixtureComponent(
            mixture_id=mixture.id,
            component_type=ComponentType.SUBSTANCE,
            substance_id=substance.id,
            concentration=50.0
        )
        db.session.add(component)
        db.session.commit()
        
        # Ověřit
        assert len(mixture.components) == 1
        assert mixture.components[0].component_type == ComponentType.SUBSTANCE
        assert mixture.components[0].substance_id == substance.id


def test_create_mixture_with_mixture(app):
    """Test vytvoření směsi obsahující jinou směs."""
    with app.app_context():
        # Vytvořit látku
        substance = Substance(name="Water", cas_number="7732-18-5")
        db.session.add(substance)
        db.session.commit()
        
        # Vytvořit první směs
        mixture1 = Mixture(name="Mixture 1")
        db.session.add(mixture1)
        db.session.flush()
        
        comp1 = MixtureComponent(
            mixture_id=mixture1.id,
            component_type=ComponentType.SUBSTANCE,
            substance_id=substance.id,
            concentration=100.0
        )
        db.session.add(comp1)
        db.session.commit()
        
        # Vytvořit druhou směs obsahující první směs
        mixture2 = Mixture(name="Mixture 2")
        db.session.add(mixture2)
        db.session.flush()
        
        comp2 = MixtureComponent(
            mixture_id=mixture2.id,
            component_type=ComponentType.MIXTURE,
            component_mixture_id=mixture1.id,
            concentration=60.0
        )
        db.session.add(comp2)
        db.session.commit()
        
        # Ověřit
        assert len(mixture2.components) == 1
        assert mixture2.components[0].component_type == ComponentType.MIXTURE
        assert mixture2.components[0].component_mixture_id == mixture1.id


def test_circular_dependency_detection(app):
    """Test detekce cyklické závislosti."""
    with app.app_context():
        # Vytvořit dvě směsi
        mixture1 = Mixture(name="Mixture A")
        mixture2 = Mixture(name="Mixture B")
        db.session.add_all([mixture1, mixture2])
        db.session.flush()
        
        # Mixture A obsahuje Mixture B
        comp1 = MixtureComponent(
            mixture_id=mixture1.id,
            component_type=ComponentType.MIXTURE,
            component_mixture_id=mixture2.id,
            concentration=50.0
        )
        db.session.add(comp1)
        db.session.commit()
        
        # Pokus o přidání Mixture A do Mixture B (cyklus)
        with pytest.raises(ValueError, match="cyklick"):
            MixtureService.validate_no_circular_dependency(mixture2.id, mixture1.id)


def test_expand_mixture_components(app):
    """Test rozbalení směsí na látky."""
    with app.app_context():
        # Vytvořit látky
        sub1 = Substance(name="Substance 1", cas_number="1-1-1")
        sub2 = Substance(name="Substance 2", cas_number="2-2-2")
        db.session.add_all([sub1, sub2])
        db.session.commit()
        
        # Vytvořit Mixture A: 50% sub1, 50% sub2
        mixA = Mixture(name="Mixture A")
        db.session.add(mixA)
        db.session.flush()
        
        db.session.add(MixtureComponent(
            mixture_id=mixA.id,
            component_type=ComponentType.SUBSTANCE,
            substance_id=sub1.id,
            concentration=50.0
        ))
        db.session.add(MixtureComponent(
            mixture_id=mixA.id,
            component_type=ComponentType.SUBSTANCE,
            substance_id=sub2.id,
            concentration=50.0
        ))
        db.session.commit()
        
        # Vytvořit Mixture B: 60% Mixture A, 40% sub2
        mixB = Mixture(name="Mixture B")
        db.session.add(mixB)
        db.session.flush()
        
        db.session.add(MixtureComponent(
            mixture_id=mixB.id,
            component_type=ComponentType.MIXTURE,
            component_mixture_id=mixA.id,
            concentration=60.0
        ))
        db.session.add(MixtureComponent(
            mixture_id=mixB.id,
            component_type=ComponentType.SUBSTANCE,
            substance_id=sub2.id,
            concentration=40.0
        ))
        db.session.commit()
        
        # Rozbalit Mixture B
        expanded = MixtureService.expand_mixture_components(mixB.id)
        
        # Ověřit výsledky
        # Mixture B obsahuje:
        # - 60% Mixture A (která obsahuje 50% sub1 + 50% sub2)
        #   = 30% sub1 + 30% sub2
        # - 40% sub2
        # Celkem: 30% sub1 + 70% sub2
        
        assert len(expanded) == 2
        
        sub1_conc = next(e['concentration'] for e in expanded if e['substance_id'] == sub1.id)
        sub2_conc = next(e['concentration'] for e in expanded if e['substance_id'] == sub2.id)
        
        assert abs(sub1_conc - 30.0) < 0.01
        assert abs(sub2_conc - 70.0) < 0.01


def test_self_reference_prevention(app):
    """Test zabránění přidání směsi do sebe sama."""
    with app.app_context():
        mixture = Mixture(name="Self-referencing Mixture")
        db.session.add(mixture)
        db.session.flush()
        
        with pytest.raises(ValueError, match="sama sebe"):
            MixtureService.validate_no_circular_dependency(mixture.id, mixture.id)
