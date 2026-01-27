"""
Formuláře pro autentizaci.

Obsahuje formulář pro přihlášení.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """
    Formulář pro přihlášení uživatele.
    """
    username = StringField("Uživatelské jméno", validators=[DataRequired()])
    password = PasswordField("Heslo", validators=[DataRequired()])
    remember = BooleanField("Zapamatovat si mě")
