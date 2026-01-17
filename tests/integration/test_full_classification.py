import pytest
from app.models import Substance, Mixture, MixtureComponent
from app.extensions import db


def test_substance_creation_and_validation(auth_client, app):
    """Test vytvoření látky a validaci polí."""
    # 1. Platná látka
    response = auth_client.post(
        "/substance/new",
        data={
            "name": "Propyl alcohol",
            "cas_number": "71-23-8",
            "ghs_codes": "GHS02, GHS05, GHS07",
            "health_h_phrases": [
                "H302",
                "H318",
                "H336",
            ],  # Formuláře posílají seznamy pro checkboxy
            "ate_oral": 1870,
            "ate_dermal": 0,
            "ate_inhalation_vapours": 0,
            "ate_inhalation_dusts_mists": 0,
            "ate_inhalation_gases": 0,
            "m_factor_acute": 1,
            "m_factor_chronic": 1,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        sub = Substance.query.filter_by(name="Propyl alcohol").first()
        assert sub is not None
        assert sub.cas_number == "71-23-8"

    # 2. Neplatný CAS (validace v modelu)
    with pytest.raises(ValueError, match="Neplatný formát CAS"):
        with app.app_context():
            sub_invalid = Substance(name="Invalid CAS", cas_number="123-45")
            db.session.add(sub_invalid)
            db.session.commit()

    # 3. Záporné ATE (validace v modelu)
    with pytest.raises(ValueError, match="ate_oral nesmí být záporné číslo"):
        with app.app_context():
            sub_invalid_ate = Substance(name="Invalid ATE", ate_oral=-50)
            db.session.add(sub_invalid_ate)
            db.session.commit()


def test_full_mixture_classification_workflow(auth_client, app):
    """Test kompletního průchodu vytvoření směsi a její klasifikace."""
    with app.app_context():
        # Vytvoření testovacích látek
        s1 = Substance(
            name="Látka A", health_h_phrases="H314", ate_oral=500
        )  # Skin Corr. 1
        s2 = Substance(
            name="Látka B", health_h_phrases="H318", ate_oral=200
        )  # Eye Dam. 1
        db.session.add_all([s1, s2])
        db.session.commit()
        s1_id, s2_id = s1.id, s2.id

    # Vytvoření směsi (3% Látka A, 10% Látka B)
    # Skin: 3% < 5% (Skin Corr 1) -> No H314
    # Eye: 3% (Skin 1) + 10% (Eye 1) = 13% >= 3% -> Eye Dam 1 (H318)
    response = auth_client.post(
        "/mixture/new",
        data={
            "name": "Testovací Směs",
            "substance_id": [s1_id, s2_id],
            "concentration": [3.0, 10.0],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        mixture = Mixture.query.filter_by(name="Testovací Směs").first()
        assert mixture is not None
        assert "H318" in mixture.final_health_hazards
        assert "H314" not in mixture.final_health_hazards
        assert "H314" not in mixture.final_health_hazards
        assert "GHS05" in mixture.final_ghs_codes

        # Ověření P-vět pro H318 (P280, P305+P351+P338, P310)
        assert "P280" in mixture.final_precautionary_statements
        assert "P310" in mixture.final_precautionary_statements

        # Ověření ATEmix (oral)
        # 100 / ATEmix = 3/500 + 10/200 = 0.006 + 0.05 = 0.056
        # ATEmix = 100 / 0.056 = 1785.7
        assert abs(mixture.final_atemix_oral - 1785.7) < 0.1


def test_invalid_concentration_validation(auth_client, app):
    """Test validace neplatné koncentrace."""
    with app.app_context():
        s = Substance(name="Sub", ate_oral=100)
        db.session.add(s)
        db.session.commit()
        s_id = s.id

    # Test > 100%
    with pytest.raises(ValueError, match="Koncentrace musí být v rozsahu"):
        with app.app_context():
            comp = MixtureComponent(
                mixture_id=1, substance_id=s_id, concentration=150.0
            )
            db.session.add(comp)
            db.session.commit()


def test_unauthenticated_access(client):
    """Test přístupu nepři hlášeného uživatele."""
    response = client.post(
        "/substance/new", data={"name": "Anon"}, follow_redirects=False
    )
    # Flask-Login přesměruje na login
    assert response.status_code == 302
    assert "/login" in response.location
