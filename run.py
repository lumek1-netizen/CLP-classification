from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Debug mode pouze v development prostředí
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode)
