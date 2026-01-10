from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models.user import User

class UserCreateForm(FlaskForm):
    username = StringField("Uživatelské jméno", validators=[
        DataRequired(message="Uživatelské jméno je povinné."),
        Length(min=3, max=80, message="Jméno musí mít 3 až 80 znaků.")
    ])
    password = PasswordField("Heslo", validators=[
        DataRequired(message="Heslo je povinné."),
        Length(min=6, message="Heslo musí mít alespoň 6 znaků.")
    ])
    confirm_password = PasswordField("Potvrzení hesla", validators=[
        DataRequired(message="Potvrzení hesla je povinné."),
        EqualTo("password", message="Hesla se musí shodovat.")
    ])
    role_id = SelectField("Role", coerce=int, validators=[DataRequired()])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Toto uživatelské jméno je již obsazeno.")
