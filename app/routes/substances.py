from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.utils.security import editor_required
from app.extensions import db
from app.models import Substance
from app.forms.substance import SubstanceForm
from app.services.substance_service import SubstanceService
from app.services.validation import validate_substance, check_duplicate_cas, ValidationMessage
from app.constants.clp import HEALTH_H_PHRASES, ENV_H_PHRASES, SCL_HAZARD_CATEGORIES
from sqlalchemy.exc import IntegrityError
from flask import jsonify
from app.services.echa_service import ECHAService

substances_bp = Blueprint("substances", __name__)


@substances_bp.route("/substances")
@login_required
def index():
    """Zobrazí seznam všech látek s možností vyhledávání."""
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 15

    query = Substance.query.order_by(Substance.name)
    if q:
        query = query.filter(
            (Substance.name.ilike(f"%{q}%")) | (Substance.cas_number.ilike(f"%{q}%"))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    substances = pagination.items

    return render_template(
        "substances.html",
        substances=substances,
        pagination=pagination,
        q=q,
        active_tab="substances",
    )


@substances_bp.route("/substance/new", methods=["GET", "POST"])
@login_required
@editor_required
def create():
    """Vytvoří novou látku."""
    form = SubstanceForm()
    
    if form.validate_on_submit():
        try:
            # Kontrola duplicitního CAS
            cas_number = form.cas_number.data.strip() if form.cas_number.data else None
            if cas_number:
                existing = check_duplicate_cas(cas_number)
                if existing:
                    flash(
                        f"⚠️ Látka s CAS {cas_number} již existuje jako '{existing.name}'",
                        "warning"
                    )
            
            # Vytvoření látky pomocí service layer
            new_substance = SubstanceService.create_substance_from_form(request.form)
            
            # Validace látky
            validation_messages = validate_substance(new_substance)
            for msg in validation_messages:
                if msg.level == ValidationMessage.LEVEL_ERROR:
                    flash(f"❌ {msg.message}", "danger")
                elif msg.level == ValidationMessage.LEVEL_WARNING:
                    flash(f"⚠️ {msg.message}. {msg.suggestion or ''}", "warning")
                elif msg.level == ValidationMessage.LEVEL_INFO:
                    flash(f"💡 {msg.message}. {msg.suggestion or ''}", "info")
            
            db.session.add(new_substance)
            db.session.commit()
            flash(f"Látka '{new_substance.name}' byla vytvořena.", "success")
            return redirect(url_for("substances.index"))
            
        except ValueError as e:
            flash(f"Neplatná data: {e}", "warning")
        except IntegrityError:
            db.session.rollback()
            flash("Látka s tímto názvem nebo CAS již existuje.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Neočekávaná chyba: {e}", "danger")

    return render_template(
        "substance_form.html",
        form=form,
        substance=None,
        health_h_phrases=HEALTH_H_PHRASES,
        env_h_phrases=ENV_H_PHRASES,
        selected_health_h_phrases=[],
        selected_env_h_phrases=[],
        scl_hazard_categories=SCL_HAZARD_CATEGORIES,
        active_tab="substances",
    )



@substances_bp.route("/substance/<int:substance_id>/edit", methods=["GET", "POST"])
@login_required
@editor_required
def edit(substance_id):
    substance = db.get_or_404(Substance, substance_id)
    form = SubstanceForm(obj=substance)

    if request.method == 'POST':
        try:
            # Aktualizace látky pomocí service layer
            SubstanceService.update_substance_from_form(substance, request.form)
            
            db.session.commit()
            flash(f"Látka '{substance.name}' byla aktualizována.", "success")
            return redirect(url_for("substances.index"))
            
        except ValueError as e:
            flash(f"Neplatná data: {e}", "warning")
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {e}", "danger")




    selected_health = (
        [h.strip() for h in substance.health_h_phrases.split(",")]
        if substance.health_h_phrases
        else []
    )
    selected_env = (
        [h.strip() for h in substance.env_h_phrases.split(",")]
        if substance.env_h_phrases
        else []
    )

    from app.models.audit import AuditLog
    audit_logs = AuditLog.query.filter_by(
        entity_type='substance', 
        entity_id=substance_id
    ).order_by(AuditLog.timestamp.desc()).all()

    return render_template(
        "substance_form.html",
        form=form,
        substance=substance,
        health_h_phrases=HEALTH_H_PHRASES,
        env_h_phrases=ENV_H_PHRASES,
        selected_health_h_phrases=selected_health,
        selected_env_h_phrases=selected_env,
        scl_hazard_categories=SCL_HAZARD_CATEGORIES,
        active_tab="substances",
        audit_logs=audit_logs,
    )


@substances_bp.route("/substance/<int:substance_id>/delete", methods=["POST"])
@login_required
@editor_required
def delete(substance_id):
    substance = db.get_or_404(Substance, substance_id)
    if substance.components:
        flash("Nelze smazat látku, která je součástí směsí.", "danger")
    else:
        db.session.delete(substance)
        db.session.commit()
        flash("Látka byla smazána.", "success")
    return redirect(url_for("substances.index"))


@substances_bp.route("/substances/fetch-echa", methods=["POST"])
@login_required
@editor_required
def fetch_echa():
    """Proxy endpoint pro získání dat z ECHA API."""
    data = request.get_json()
    cas_or_ec = data.get("query", "").strip()
    
    if not cas_or_ec:
        return jsonify({"error": "Chybí dotaz (CAS/EC)."}), 400
        
    echa_service = ECHAService()
    result = echa_service.fetch_data(cas_or_ec)
    
    if "error" in result:
        return jsonify(result), 404
        
    return jsonify(result)
