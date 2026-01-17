from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.forms.auth import LoginForm
from app.extensions import db, limiter
from urllib.parse import urlparse

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # NOVÉ: Max 5 pokusů za minutu
def login():
    if current_user.is_authenticated:
        return redirect(url_for("mixtures.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if not user or not user.check_password(form.password.data):
            flash("Neplatné uživatelské jméno nebo heslo.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember.data)

        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("mixtures.index")
        return redirect(next_page)

    return render_template("login.html", form=form, active_tab="login")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Byl jste úspěšně odhlášen.", "info")
    return redirect(url_for("auth.login"))
