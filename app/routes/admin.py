from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.user import User
from app.models.role import Role
from app.models.audit import AuditLog
from app.extensions import db
from app.utils.security import admin_required
from app.forms.admin import UserCreateForm

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/users", methods=["GET", "POST"])
@login_required
@admin_required
def users():
    users = User.query.all()
    roles = Role.query.all()
    form = UserCreateForm()
    form.role_id.choices = [(r.id, r.name.capitalize()) for r in roles]
    
    if form.validate_on_submit():
        new_user = User(username=form.username.data, role_id=form.role_id.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Uživatel {new_user.username} byl úspěšně vytvořen.", "success")
        return redirect(url_for("admin.users"))
        
    return render_template("admin/users.html", users=users, roles=roles, form=form, active_tab="admin_users")

@admin_bp.route("/admin/audit-log")
@login_required
@admin_required
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template("admin/audit_log.html", logs=logs, active_tab="admin_audit")

@admin_bp.route("/admin/user/<int:user_id>/update_role", methods=["POST"])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    role_id = request.form.get("role_id")
    
    if not role_id:
        flash("Nenalezena žádná role k přiřazení.", "danger")
        return redirect(url_for("admin.users"))
        
    user.role_id = int(role_id)
    db.session.commit()
    flash(f"Role uživatele {user.username} byla aktualizována.", "success")
    return redirect(url_for("admin.users"))

@admin_bp.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Ochrana: Nelze smazat admina přes webové rozhraní (ani sebe sama)
    if user.has_role('admin'):
        flash(f"Uživatele s rolí 'Admin' (včetně {user.username}) nelze smazat z bezpečnostních důvodů.", "danger")
        return redirect(url_for("admin.users"))
        
    if user.id == current_user.id:
        flash("Nemůžete smazat svůj vlastní účet.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"Uživatel {user.username} byl úspěšně odstraněn.", "success")
    return redirect(url_for("admin.users"))
