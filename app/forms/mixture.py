from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class MixtureForm(FlaskForm):
    name = StringField("Název směsi", validators=[DataRequired(), Length(max=100)])
    # Komponenty se řeší dynamicky v request.form, ale CSRF token potřebujeme
