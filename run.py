import os
from app import create_app

# Načti prostředí z environment variable
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Debug mode pouze v development
    debug_mode = config_name == 'development'
    app.run(debug=debug_mode)
