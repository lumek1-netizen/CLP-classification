from app import create_app
from app.extensions import db
from app.models.user import User
import sys

def create_admin(username, password):
    app = create_app()
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"Uživatel {username} již existuje.")
            return

        new_user = User(username=username, is_admin=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        print(f"Admin uživatel {username} byl úspěšně vytvořen.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Použití: python create_admin.py <username> <password>")
    else:
        create_admin(sys.argv[1], sys.argv[2])
