from flask import Flask, render_template, request
from .config import get_config
from .extensions import db, migrate, csrf


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    
    # Načti konfiguraci podle prostředí
    config = get_config(config_name)
    app.config.from_object(config)

    # === Nastav logging ===
    from .logging_config import setup_logging
    setup_logging(app)

    # === Bezpečnostní hlavičky ===
    from .security import init_security_headers, init_session_security
    init_security_headers(app)
    init_session_security(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # === NOVÉ: Rate Limiter ===
    from .extensions import limiter
    limiter.init_app(app)
    # ==========================
    
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
    from .routes.health import health_bp

    app.register_blueprint(substances_bp)
    app.register_blueprint(mixtures_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.warning(f'404 Error: {e}')
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f'500 Error: {e}', exc_info=True)
        return render_template("errors/500.html"), 500
    
    # === NOVÉ: Rate Limit Error ===
    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f'Rate limit exceeded: {request.remote_addr}')
        return render_template("errors/429.html", error=e), 429

    return app

