from app.extensions import db
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=True)
    
    role = db.relationship("Role", backref=db.backref("users", lazy=True))

    @property
    def is_admin(self):
        return self.role is not None and self.role.name == "admin"

    def has_role(self, role_names):
        if isinstance(role_names, str):
            role_names = [role_names]
        return self.role is not None and self.role.name in role_names

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class AnonymousUser(AnonymousUserMixin):
    def has_role(self, role_names):
        return False

    @property
    def is_admin(self):
        return False

