from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Mixture, Substance, MixtureComponent
from app.services.clp import run_clp_classification
from app.constants.clp import H_PHRASES_DISPLAY
from sqlalchemy.exc import IntegrityError

mixtures_bp = Blueprint('mixtures', __name__)

@mixtures_bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    if q:
        mixtures = Mixture.query.filter(Mixture.name.ilike(f'%{q}%')).order_by(Mixture.created_date.desc()).all()
    else:
        mixtures = Mixture.query.order_by(Mixture.created_date.desc()).all()
    return render_template('index.html', mixtures=mixtures, q=q, active_tab='mixtures')

@mixtures_bp.route('/mixture/new', methods=['GET', 'POST'])
def create():
    substance_data = [s.to_dict() for s in Substance.query.order_by(Substance.name).all()]
    if request.method == 'POST':
        try:
            name = request.form.get('name').strip()
            concs = request.form.getlist('concentration')
            sub_ids = request.form.getlist('substance_id')
            
            components = []
            total = 0.0
            seen = set()

            for c_str, s_id_str in zip(concs, sub_ids):
                if not c_str or not s_id_str: continue
                c, s_id = float(c_str), int(s_id_str)
                if c <= 0: raise ValueError("Koncentrace musí být kladná.")
                if s_id in seen: raise ValueError("Duplicitní složka.")
                total += c
                if total > 100.001: raise ValueError("Celkem přes 100 %.")
                components.append({'substance_id': s_id, 'concentration': c})
                seen.add(s_id)

            if not components: raise ValueError("Směs musí mít aspoň jednu složku.")

            new_mixture = Mixture(name=name)
            db.session.add(new_mixture)
            db.session.flush()

            for comp in components:
                db.session.add(MixtureComponent(mixture_id=new_mixture.id, **comp))
            
            db.session.commit()
            run_clp_classification(new_mixture)
            db.session.commit()

            flash(f"Směs '{name}' vytvořena.", 'success')
            return redirect(url_for('mixtures.detail', mixture_id=new_mixture.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {str(e)}", 'danger')

    return render_template('mixture_form.html', substances=substance_data, mixture=None, 
                           existing_components=[{}], active_tab='mixtures')

@mixtures_bp.route('/mixture/<int:mixture_id>')
def detail(mixture_id):
    mixture = db.get_or_404(Mixture, mixture_id)
    comp_details = []
    total = 0.0
    for comp in mixture.components:
        comp_details.append({
            'substance_name': comp.substance.name,
            'concentration': comp.concentration,
            'hazards': comp.substance.health_h_phrases,
            'env_hazards': comp.substance.env_h_phrases,
        })
        total += comp.concentration
    return render_template('mixture_detail.html', mixture=mixture, components=comp_details, 
                           total_concentration=total, h_phrases_display=H_PHRASES_DISPLAY, active_tab='mixtures')

@mixtures_bp.route('/mixture/<int:mixture_id>/edit', methods=['GET', 'POST'])
def edit(mixture_id):
    mixture = db.get_or_404(Mixture, mixture_id)
    substance_data = [s.to_dict() for s in Substance.query.order_by(Substance.name).all()]
    existing = [{'substance_id': c.substance_id, 'concentration': c.concentration} for c in mixture.components]

    if request.method == 'POST':
        try:
            mixture.name = request.form.get('name').strip()
            concs = request.form.getlist('concentration')
            sub_ids = request.form.getlist('substance_id')
            
            components = []
            total = 0.0
            seen = set()
            for c_str, s_id_str in zip(concs, sub_ids):
                if not c_str or not s_id_str: continue
                c, s_id = float(c_str), int(s_id_str)
                total += c
                if total > 100.001: raise ValueError("Celkem přes 100 %.")
                components.append({'substance_id': s_id, 'concentration': c})
                seen.add(s_id)

            MixtureComponent.query.filter_by(mixture_id=mixture.id).delete()
            for comp in components:
                db.session.add(MixtureComponent(mixture_id=mixture.id, **comp))
            
            db.session.commit()
            run_clp_classification(mixture)
            db.session.commit()
            flash("Směs aktualizována.", 'success')
            return redirect(url_for('mixtures.detail', mixture_id=mixture.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {str(e)}", 'danger')

    return render_template('mixture_form.html', substances=substance_data, mixture=mixture, 
                           existing_components=existing, active_tab='mixtures')

@mixtures_bp.route('/mixture/<int:mixture_id>/delete', methods=['POST'])
def delete(mixture_id):
    mixture = db.get_or_404(Mixture, mixture_id)
    db.session.delete(mixture)
    db.session.commit()
    flash("Směs smazána.", 'success')
    return redirect(url_for('mixtures.index'))
