from flask import Flask, render_template
from .config import Config
from .extensions import db, migrate, csrf


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    from .extensions import cache

    cache.init_app(app)

    from .extensions import login_manager

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Pro přístup k této stránce se prosím přihlaste."
    login_manager.login_message_category = "info"

    from .services.audit_service import register_audit_listeners
    register_audit_listeners()

    from .models.user import User, AnonymousUser

    login_manager.anonymous_user = AnonymousUser

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes.substances import substances_bp
    from .routes.mixtures import mixtures_bp
    from .routes.data import data_bp
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp

    app.register_blueprint(substances_bp)
    app.register_blueprint(mixtures_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    return app
