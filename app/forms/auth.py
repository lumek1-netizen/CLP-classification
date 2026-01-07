from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Uživatelské jméno", validators=[DataRequired()])
    password = PasswordField("Heslo", validators=[DataRequired()])
    remember = BooleanField("Zapamatovat si mě")
