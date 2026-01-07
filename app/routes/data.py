from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    current_app,
)
from flask_login import login_required
import io
import json
from datetime import datetime
from app.extensions import db
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification

data_bp = Blueprint("data", __name__)


@data_bp.route("/data/management")
@login_required
def management():
    return render_template("data_management.html", active_tab="data_management")


@data_bp.route("/data/export")
@login_required
def export_data():
    substances = Substance.query.all()
    mixtures = Mixture.query.all()
    data = {
        "substances": [s.to_dict() for s in substances],
        "mixtures": [m.to_dict() for m in mixtures],
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
    }
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    bytes_io = io.BytesIO(json_data.encode("utf-8"))
    return send_file(
        bytes_io,
        mimetype="application/json",
        as_attachment=True,
        download_name=f'clp_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
    )


@data_bp.route("/data/import", methods=["POST"])
@login_required
def import_data():
    if "file" not in request.files:
        flash("Nebyl vybrán soubor.", "danger")
        return redirect(url_for("data.management"))

    file = request.files["file"]
    if file.filename == "":
        flash("Nebyl vybrán soubor.", "danger")
        return redirect(url_for("data.management"))

    try:
        data = json.loads(file.read().decode("utf-8"))
        sub_count = 0
        mix_count = 0

        for s_data in data.get("substances", []):
            if not Substance.query.filter_by(name=s_data["name"]).first():
                db.session.add(Substance(**s_data))
                sub_count += 1
        db.session.commit()

        for m_data in data.get("mixtures", []):
            if not Mixture.query.filter_by(name=m_data["name"]).first():
                new_mix = Mixture(name=m_data["name"])
                db.session.add(new_mix)
                db.session.flush()
                for c_data in m_data.get("components", []):
                    sub = Substance.query.filter_by(
                        name=c_data["substance_name"]
                    ).first()
                    if sub:
                        db.session.add(
                            MixtureComponent(
                                mixture_id=new_mix.id,
                                substance_id=sub.id,
                                concentration=c_data["concentration"],
                            )
                        )
                run_clp_classification(new_mix)
                mix_count += 1
        db.session.commit()
        flash(f"Importováno {sub_count} látek a {mix_count} směsí.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Chyba při importu: {str(e)}", "danger")
    return redirect(url_for("data.management"))
