"""
Inicializace Flask aplikace.

Tento modul obsahuje tovární funkci create_app, která:
1. Inicializuje aplikaci a načítá konfiguraci.
2. Nastavuje logování a bezpečnostní hlavičky.
3. Inicializuje rozšíření (DB, Migrate, CSRF, Cache, Limiter, Login).
4. Registruje blueprinty (moduly aplikace).
5. Definuje globální obsluhu chyb (404, 429, 500).
"""

from flask import Flask, render_template, request
from .config import get_config
from .extensions import db, migrate, csrf


def create_app(config_name=None):
    """Tovární funkce pro vytvoření instance aplikace."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    
    # Načtení konfigurace podle prostředí
    config = get_config(config_name)
    app.config.from_object(config)

    # === Nastavení logování ===
    from .logging_config import setup_logging
    setup_logging(app)

    # === Bezpečnostní hlavičky ===
    from .security import init_security_headers, init_session_security
    init_security_headers(app)
    init_session_security(app)

    # Inicializace rozšíření
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Rate Limiter (omezení počtu požadavků)
    from .extensions import limiter
    limiter.init_app(app)
    
    from .extensions import cache
    cache.init_app(app)

    # === Content Security Policy (Talisman) ===
    from .extensions import talisman
    csp = {
        'default-src': '\'self\'',
        'script-src': ['\'self\'', 'https://cdn.jsdelivr.net'],
        'style-src': ['\'self\'', 'https://fonts.googleapis.com'],
        'font-src': ['\'self\'', 'https://fonts.gstatic.com'],
        'img-src': ['\'self\'', 'data:'],
    }
    talisman.init_app(
        app, 
        content_security_policy=csp, 
        content_security_policy_nonce_in=['script-src']
    )

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

    # Registrace blueprintů (moduly aplikace)
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

    # Obsluha chyb (Error Handlers)
    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.warning(f'404 Error: {e}')
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f'500 Error: {e}', exc_info=True)
        return render_template("errors/500.html"), 500
    
    # Obsluha překročení rate limitu (Too Many Requests)
    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f'Rate limit exceeded: {request.remote_addr}')
        return render_template("errors/429.html", error=e), 429

    return app

