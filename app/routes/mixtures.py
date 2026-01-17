from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_
from flask_login import login_required
from app.utils.security import editor_required
from app.extensions import db
from app.models import Mixture, Substance, MixtureComponent
from app.forms.mixture import MixtureForm
from app.services.clp import run_clp_classification
from app.services.mixture_service import MixtureService
from app.constants.clp import H_PHRASES_DISPLAY
from app.constants.p_phrases import ALL_P_PHRASES
from sqlalchemy.exc import IntegrityError

mixtures_bp = Blueprint("mixtures", __name__)


@mixtures_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Mixture.query.order_by(Mixture.created_date.desc())
    if q:
        query = (
            query.outerjoin(Mixture.components)
            .outerjoin(MixtureComponent.substance)
            .filter(
                or_(
                    Mixture.name.ilike(f"%{q}%"),
                    Substance.name.ilike(f"%{q}%"),
                    Substance.cas_number.ilike(f"%{q}%"),
                )
            )
            .distinct()
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    mixtures = pagination.items

    return render_template(
        "index.html",
        mixtures=mixtures,
        pagination=pagination,
        q=q,
        active_tab="mixtures",
    )


@mixtures_bp.route("/mixture/new", methods=["GET", "POST"])
@login_required
@editor_required
def create():
    form = MixtureForm()
    substance_data = [
        s.to_dict() for s in Substance.query.order_by(Substance.name).all()
    ]
    if form.validate_on_submit():
        try:
            name = form.name.data.strip()
            
            # Parsování a validace komponent pomocí service layer
            components = MixtureService.parse_and_validate_components(request.form)


            new_mixture = Mixture(name=name, ph=form.ph.data)
            db.session.add(new_mixture)
            db.session.flush()

            for comp in components:
                db.session.add(MixtureComponent(mixture_id=new_mixture.id, **comp))

            db.session.commit()
            run_clp_classification(new_mixture)
            db.session.commit()

            flash(f"Směs '{name}' byla vytvořena.", "success")
            return redirect(url_for("mixtures.detail", mixture_id=new_mixture.id))
            
        except ValueError as e:
            # Validační chyba - očekávaná
            flash(f"Neplatná data: {e}", "warning")
        except IntegrityError:
            db.session.rollback()
            flash("Směs s tímto názvem již existuje.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Neočekávaná chyba: {e}", "danger")

    return render_template(
        "mixture_form.html",
        form=form,
        substances=substance_data,
        mixture=None,
        existing_components=[{}],
        active_tab="mixtures",
    )


@mixtures_bp.route("/mixture/<int:mixture_id>")
@login_required
def detail(mixture_id):
    from sqlalchemy.orm import joinedload

    from app.models.audit import AuditLog

    mixture = (
        Mixture.query.options(
            joinedload(Mixture.components).joinedload(MixtureComponent.substance)
        )
        .filter_by(id=mixture_id)
        .first_or_404()
    )
    
    audit_logs = AuditLog.query.filter_by(
        entity_type='mixture', 
        entity_id=mixture_id
    ).order_by(AuditLog.timestamp.desc()).all()
    comp_details = []
    total = 0.0
    for comp in mixture.components:
        comp_details.append(
            {
                "substance_name": comp.substance.name,
                "concentration": comp.concentration,
                "hazards": comp.substance.health_h_phrases,
                "env_hazards": comp.substance.env_h_phrases,
            }
        )
        total += comp.concentration
    return render_template(
        "mixture_detail.html",
        mixture=mixture,
        components=comp_details,
        total_concentration=total,
        h_phrases_display=H_PHRASES_DISPLAY,
        p_phrases_text=ALL_P_PHRASES,
        active_tab="mixtures",
        audit_logs=audit_logs,
    )


@mixtures_bp.route("/mixture/<int:mixture_id>/edit", methods=["GET", "POST"])
@login_required
@editor_required
def edit(mixture_id):
    mixture = db.get_or_404(Mixture, mixture_id)
    form = MixtureForm(obj=mixture)
    substance_data = [
        s.to_dict() for s in Substance.query.order_by(Substance.name).all()
    ]
    existing = [
        {"substance_id": c.substance_id, "concentration": c.concentration}
        for c in mixture.components
    ]

    if form.validate_on_submit():
        try:
            mixture.name = form.name.data.strip()
            mixture.ph = form.ph.data
            
            # Parsování a validace komponent pomocí service layer
            components = MixtureService.parse_and_validate_components(request.form)

            # Odstranění starých komponent
            MixtureComponent.query.filter_by(mixture_id=mixture.id).delete()
            
            # Přidání nových komponent
            for comp in components:
                db.session.add(MixtureComponent(mixture_id=mixture.id, **comp))

            db.session.commit()
            
            # Reklasifikace
            run_clp_classification(mixture)
            db.session.commit()
            
            flash("Směs byla aktualizována.", "success")
            return redirect(url_for("mixtures.detail", mixture_id=mixture.id))
            
        except ValueError as e:
            flash(f"Neplatná data: {e}", "warning")
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {e}", "danger")

    return render_template(
        "mixture_form.html",
        form=form,
        substances=substance_data,
        mixture=mixture,
        existing_components=existing,
        active_tab="mixtures",
    )


@mixtures_bp.route("/mixture/<int:mixture_id>/delete", methods=["POST"])
@login_required
@editor_required
def delete(mixture_id):
    mixture = db.get_or_404(Mixture, mixture_id)
    db.session.delete(mixture)
    db.session.commit()
    flash("Směs smazána.", "success")
    return redirect(url_for("mixtures.index"))
