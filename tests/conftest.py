import pytest
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Substance, User


@pytest.fixture
def app():
    # Použijeme in-memory SQLite pro testy
    # Musíme předat konfiguraci přímo do create_app, aby se engine vytvořil správně
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-key",
    }
    
    class TestConfig(Config):
        pass
    
    for key, value in test_config.items():
        setattr(TestConfig, key, value)

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, app):
    # Vytvoření testovacího uživatele a přihlášení
    with app.app_context():
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()

    client.post(
        "/login",
        data={"username": "testuser", "password": "testpass"},
        follow_redirects=True,
    )
    return client


@pytest.fixture
def sample_substance(app):
    with app.app_context():
        substance = Substance(
            name="Test Substance", ate_oral=500, health_h_phrases="H302"
        )
        db.session.add(substance)
        db.session.commit()
        return substance
