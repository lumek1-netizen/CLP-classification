from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.utils.security import editor_required
from app.extensions import db
from app.models import Substance
from app.forms.substance import SubstanceForm
from app.services.clp import get_float_or_none, get_int_or_default
from app.services.validation import validate_substance, check_duplicate_cas, ValidationMessage
from app.constants.clp import HEALTH_H_PHRASES, ENV_H_PHRASES, SCL_HAZARD_CATEGORIES
from sqlalchemy.exc import IntegrityError

substances_bp = Blueprint("substances", __name__)


@substances_bp.route("/substances")
@login_required
def index():
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
    form = SubstanceForm()
    if form.validate_on_submit():
        try:
            health_list = request.form.getlist("health_h_phrases")
            env_list = request.form.getlist("env_h_phrases")

            # Kontrola duplicitního CAS
            cas_number = form.cas_number.data.strip() if form.cas_number.data else None
            if cas_number:
                existing = check_duplicate_cas(cas_number)
                if existing:
                    flash(f"⚠️ Látka s CAS {cas_number} již existuje jako '{existing.name}'", "warning")
                    # Pokračujeme, ale upozorníme uživatele

            new_substance = Substance(
                name=form.name.data.strip(),
                cas_number=cas_number,
                ghs_codes=form.ghs_codes.data.strip() if form.ghs_codes.data else None,
                health_h_phrases=", ".join(health_list) if health_list else None,
                env_h_phrases=", ".join(env_list) if env_list else None,
                ate_oral=form.ate_oral.data,
                ate_dermal=form.ate_dermal.data,
                ate_inhalation_vapours=form.ate_inhalation_vapours.data,
                ate_inhalation_dusts_mists=form.ate_inhalation_dusts_mists.data,
                ate_inhalation_gases=form.ate_inhalation_gases.data,
                m_factor_acute=form.m_factor_acute.data or 1,
                m_factor_chronic=form.m_factor_chronic.data or 1,
                scl_limits=request.form.get("scl_data", ""),
                is_lact=form.is_lact.data,
                ed_hh_cat=form.ed_hh_cat.data if form.ed_hh_cat.data > 0 else None,
                ed_env_cat=form.ed_env_cat.data if form.ed_env_cat.data > 0 else None,
                is_pbt=form.is_pbt.data,
                is_vpvb=form.is_vpvb.data,
                is_pmt=form.is_pmt.data,
                is_vpvm=form.is_vpvm.data,
                has_ozone=form.has_ozone.data,
            )
            
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
        except IntegrityError:
            db.session.rollback()
            flash("Látka s tímto názvem nebo CAS již existuje.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {str(e)}", "danger")

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

    if form.validate_on_submit():
        try:
            substance.name = form.name.data.strip()
            substance.cas_number = (
                form.cas_number.data.strip() if form.cas_number.data else None
            )
            substance.ghs_codes = (
                form.ghs_codes.data.strip() if form.ghs_codes.data else None
            )

            health_list = request.form.getlist("health_h_phrases")
            env_list = request.form.getlist("env_h_phrases")
            substance.health_h_phrases = ", ".join(health_list) if health_list else None
            substance.env_h_phrases = ", ".join(env_list) if env_list else None

            substance.ate_oral = form.ate_oral.data
            substance.ate_dermal = form.ate_dermal.data
            substance.ate_inhalation_vapours = form.ate_inhalation_vapours.data
            substance.ate_inhalation_dusts_mists = form.ate_inhalation_dusts_mists.data
            substance.ate_inhalation_gases = form.ate_inhalation_gases.data
            substance.m_factor_acute = form.m_factor_acute.data or 1
            substance.m_factor_chronic = form.m_factor_chronic.data or 1
            substance.scl_limits = request.form.get("scl_data", "")

            substance.is_lact = form.is_lact.data
            substance.ed_hh_cat = form.ed_hh_cat.data if form.ed_hh_cat.data > 0 else None
            substance.ed_env_cat = form.ed_env_cat.data if form.ed_env_cat.data > 0 else None
            substance.is_pbt = form.is_pbt.data
            substance.is_vpvb = form.is_vpvb.data
            substance.is_pmt = form.is_pmt.data
            substance.is_vpvm = form.is_vpvm.data
            substance.has_ozone = form.has_ozone.data

            db.session.commit()
            flash(f"Látka '{substance.name}' byla aktualizována.", "success")
            return redirect(url_for("substances.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {str(e)}", "danger")

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
