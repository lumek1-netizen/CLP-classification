from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Substance
from app.services.clp import get_float_or_none, get_int_or_default
from app.constants.clp import HEALTH_H_PHRASES, ENV_H_PHRASES, SCL_HAZARD_CATEGORIES
from sqlalchemy.exc import IntegrityError

substances_bp = Blueprint('substances', __name__)

@substances_bp.route('/substances')
def index():
    q = request.args.get('q', '').strip()
    if q:
        substances = Substance.query.filter(
            (Substance.name.ilike(f'%{q}%')) | 
            (Substance.cas_number.ilike(f'%{q}%'))
        ).order_by(Substance.name).all()
    else:
        substances = Substance.query.order_by(Substance.name).all()
    return render_template('substances.html', substances=substances, q=q, active_tab='substances')

@substances_bp.route('/substance/new', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            cas = request.form.get('cas_number', '').strip()
            health_list = request.form.getlist('health_h_phrases')
            env_list = request.form.getlist('env_h_phrases')
            
            new_substance = Substance(
                name=name,
                cas_number=cas if cas else None,
                ghs_codes=request.form.get('ghs_codes', '').strip(),
                health_h_phrases=', '.join(health_list) if health_list else None,
                env_h_phrases=', '.join(env_list) if env_list else None,
                ate_oral=get_float_or_none(request.form.get('ate_oral')),
                ate_dermal=get_float_or_none(request.form.get('ate_dermal')),
                ate_inhalation_vapours=get_float_or_none(request.form.get('ate_inhalation_vapours')),
                ate_inhalation_dusts_mists=get_float_or_none(request.form.get('ate_inhalation_dusts_mists')),
                ate_inhalation_gases=get_float_or_none(request.form.get('ate_inhalation_gases')),
                m_factor_acute=get_int_or_default(request.form.get('m_factor_acute')),
                m_factor_chronic=get_int_or_default(request.form.get('m_factor_chronic')),
                scl_limits=request.form.get('scl_data', '')
            )
            db.session.add(new_substance)
            db.session.commit()
            flash(f"Látka '{name}' byla vytvořena.", 'success')
            return redirect(url_for('substances.index'))
        except IntegrityError:
            db.session.rollback()
            flash("Látka s tímto názvem nebo CAS již existuje.", 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {str(e)}", 'danger')

    return render_template('substance_form.html', 
                           substance=None, health_h_phrases=HEALTH_H_PHRASES,
                           env_h_phrases=ENV_H_PHRASES, selected_health_h_phrases=[],
                           selected_env_h_phrases=[], scl_hazard_categories=SCL_HAZARD_CATEGORIES, 
                           active_tab='substances')

@substances_bp.route('/substance/<int:substance_id>/edit', methods=['GET', 'POST'])
def edit(substance_id):
    substance = db.get_or_404(Substance, substance_id)
    if request.method == 'POST':
        try:
            substance.name = request.form.get('name', '').strip()
            substance.cas_number = request.form.get('cas_number', '').strip() or None
            substance.ghs_codes = request.form.get('ghs_codes', '').strip() or None
            
            health_list = request.form.getlist('health_h_phrases')
            env_list = request.form.getlist('env_h_phrases')
            substance.health_h_phrases = ', '.join(health_list) if health_list else None
            substance.env_h_phrases = ', '.join(env_list) if env_list else None
            
            substance.ate_oral = get_float_or_none(request.form.get('ate_oral'))
            substance.ate_dermal = get_float_or_none(request.form.get('ate_dermal'))
            substance.ate_inhalation_vapours = get_float_or_none(request.form.get('ate_inhalation_vapours'))
            substance.ate_inhalation_dusts_mists = get_float_or_none(request.form.get('ate_inhalation_dusts_mists'))
            substance.ate_inhalation_gases = get_float_or_none(request.form.get('ate_inhalation_gases'))
            substance.m_factor_acute = get_int_or_default(request.form.get('m_factor_acute'))
            substance.m_factor_chronic = get_int_or_default(request.form.get('m_factor_chronic'))
            substance.scl_limits = request.form.get('scl_data', '')

            db.session.commit()
            flash(f"Látka '{substance.name}' byla aktualizována.", 'success')
            return redirect(url_for('substances.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {str(e)}", 'danger')

    selected_health = [h.strip() for h in substance.health_h_phrases.split(',')] if substance.health_h_phrases else []
    selected_env = [h.strip() for h in substance.env_h_phrases.split(',')] if substance.env_h_phrases else []
    
    return render_template('substance_form.html', 
                           substance=substance, health_h_phrases=HEALTH_H_PHRASES,
                           env_h_phrases=ENV_H_PHRASES, selected_health_h_phrases=selected_health,
                           selected_env_h_phrases=selected_env, scl_hazard_categories=SCL_HAZARD_CATEGORIES,
                           active_tab='substances')

@substances_bp.route('/substance/<int:substance_id>/delete', methods=['POST'])
def delete(substance_id):
    substance = db.get_or_404(Substance, substance_id)
    if substance.components:
        flash("Nelze smazat látku, která je součástí směsí.", 'danger')
    else:
        db.session.delete(substance)
        db.session.commit()
        flash("Látka byla smazána.", 'success')
    return redirect(url_for('substances.index'))
