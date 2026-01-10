from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
from app.extensions import db


def test_run_clp_classification_integration(app):
    with app.app_context():
        # 1. Příprava dat
        s1 = Substance(
            name="Toxic Substance",
            ate_oral=100.0,  # Kat 3 -> H301
            health_h_phrases="H301,H315",  # H315 -> Skin Irrit 2
        )
        db.session.add(s1)
        db.session.commit()

        mix = Mixture(name="Test Classification Mix")
        db.session.add(mix)
        db.session.commit()

        comp = MixtureComponent(
            mixture_id=mix.id, substance_id=s1.id, concentration=100.0
        )
        db.session.add(comp)
        db.session.commit()

        # 2. Spuštění klasifikace
        run_clp_classification(mix)
        db.session.commit()

        # 3. Ověření výsledků
        retrieved_mix = Mixture.query.get(mix.id)
        # Tady to bývá ošidné kvůli řazení a mezerám, ale engine používá sorted a ', '
        assert "H301" in retrieved_mix.final_health_hazards
        assert "H315" in retrieved_mix.final_health_hazards
        assert retrieved_mix.final_ghs_codes == "GHS06"  # GHS06 má prioritu nad GHS07


        # 4. Ověření logu
        assert retrieved_mix.classification_log is not None
        log_data = retrieved_mix.classification_log
        assert isinstance(log_data, list)


        at_least_one_ate_step = any("ATE" in item["step"] for item in log_data)
        assert at_least_one_ate_step, "V logu chybí zmínka o ATE"
