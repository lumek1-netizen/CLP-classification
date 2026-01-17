from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User

def seed_rbac():
    app = create_app()
    with app.app_context():
        # 1. Create roles if they don't exist
        roles = {
            "admin": "Kompletní správa systému",
            "editor": "Správa odborného obsahu (látky, směsi)",
            "viewer": "Pouze prohlížení dat"
        }
        
        for name, desc in roles.items():
            role = Role.query.filter_by(name=name).first()
            if not role:
                role = Role(name=name, description=desc)
                db.session.add(role)
                print(f"Role '{name}' vytvořena.")
        
        db.session.commit()
        
        # 2. Assign 'admin' role to existing users who don't have a role
        # (Assuming all existing users should be admins for now or we map them)
        admin_role = Role.query.filter_by(name="admin").first()
        users_without_role = User.query.filter_by(role_id=None).all()
        
        for user in users_without_role:
            user.role_id = admin_role.id
            print(f"Uživateli '{user.username}' přiřazena role 'admin'.")
            
        db.session.commit()
        print("Inicializace RBAC dokončena.")

if __name__ == "__main__":
    seed_rbac()
