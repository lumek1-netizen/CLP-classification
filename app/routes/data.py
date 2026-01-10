from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    current_app,
    make_response,
)
from flask_login import login_required, current_user
from app.utils.security import admin_required
import io
import json
from datetime import datetime
from app.extensions import db
from app.models import Substance, Mixture, MixtureComponent
from app.services.clp import run_clp_classification
from app.services.import_service import import_substances_from_csv
from app.services.export_service import export_substances_to_csv, generate_csv_template

data_bp = Blueprint("data", __name__)


@data_bp.route("/data/management")
@login_required
def management():
    return render_template("data_management.html", active_tab="data_management")


@data_bp.route("/data/export")
@login_required
@admin_required
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
@admin_required
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


@data_bp.route("/data/import/substances/csv", methods=["POST"])
@login_required
@admin_required
def import_substances_csv():
    """Import látek z CSV souboru."""
    if "file" not in request.files:
        flash("Nebyl vybrán soubor.", "danger")
        return redirect(url_for("data.management"))

    file = request.files["file"]
    if file.filename == "":
        flash("Nebyl vybrán soubor.", "danger")
        return redirect(url_for("data.management"))

    # Kontrola přípony
    if not file.filename.lower().endswith('.csv'):
        flash("Soubor musí být ve formátu CSV.", "danger")
        return redirect(url_for("data.management"))

    try:
        # Import látek
        result = import_substances_from_csv(file, current_user.id if current_user else None)
        
        # Zobrazení výsledků
        if result['success'] > 0:
            flash(f"✅ Úspěšně importováno {result['success']} látek.", "success")
        
        if result['skipped'] > 0:
            flash(f"⚠️ Přeskočeno {result['skipped']} látek (duplicity).", "warning")
        
        if result['warnings']:
            for warning in result['warnings'][:5]:  # Max 5 varování
                flash(f"⚠️ {warning}", "warning")
            if len(result['warnings']) > 5:
                flash(f"... a dalších {len(result['warnings']) - 5} varování", "warning")
        
        if result['errors']:
            for error in result['errors'][:5]:  # Max 5 chyb
                flash(f"❌ {error}", "danger")
            if len(result['errors']) > 5:
                flash(f"... a dalších {len(result['errors']) - 5} chyb", "danger")
    
    except Exception as e:
        flash(f"Chyba při importu: {str(e)}", "danger")
    
    return redirect(url_for("data.management"))


@data_bp.route("/data/export/substances/csv")
@login_required
@admin_required
def export_substances_csv():
    """Export látek do CSV souboru."""
    try:
        csv_content = export_substances_to_csv()
        
        # Vytvoření response
        response = make_response(csv_content)
        response.headers["Content-Disposition"] = f"attachment; filename=substances_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        
        return response
    
    except Exception as e:
        flash(f"Chyba při exportu: {str(e)}", "danger")
        return redirect(url_for("data.management"))


@data_bp.route("/data/template/substances/csv")
@login_required
@admin_required
def download_csv_template():
    """Stáhnout CSV šablonu pro import látek."""
    try:
        csv_content = generate_csv_template()
        
        response = make_response(csv_content)
        response.headers["Content-Disposition"] = "attachment; filename=substances_template.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        
        return response
    
    except Exception as e:
        flash(f"Chyba při generování šablony: {str(e)}", "danger")
        return redirect(url_for("data.management"))
