"""
Model role.

Definuje uživatelské role pro RBAC (Role-Based Access Control).
"""
from app.extensions import db

class Role(db.Model):
    """
    Model uživatelské role (např. 'admin', 'user').
    """
    __tablename__ = "role"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Role {self.name}>"
