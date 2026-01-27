"""
Pomocné funkce pro zabezpečení a řízení přístupu.

Obsahuje dekorátory pro kontrolu rolí uživatelů.
"""
from functools import wraps
from flask import abort
from flask_login import current_user

def roles_required(role_names):
    """
    Dekorátor, který kontroluje, zda má přihlášený uživatel jednu z požadovaných rolí.
    """
    def decorator(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if not current_user.has_role(role_names):
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_view
    return decorator

def admin_required(f):
    """
    Dekorátor vyžadující roli 'admin'.
    """
    return roles_required(["admin"])(f)

def editor_required(f):
    """
    Dekorátor vyžadující roli 'admin' nebo 'editor'.
    """
    return roles_required(["admin", "editor"])(f)
