"""
Bezpečnostní middleware pro HTTP hlavičky.
"""
from flask import Flask, Response


def init_security_headers(app: Flask) -> None:
    """
    Přidá bezpečnostní HTTP hlavičky do všech responses.
    
    Dokumentace:
    - https://owasp.org/www-project-secure-headers/
    - https://securityheaders.com/
    """
    
    @app.after_request
    def set_security_headers(response: Response) -> Response:
        """Nastaví bezpečnostní hlavičky pro každý response."""
        
        # === X-Content-Type-Options ===
        # Prevence MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # === X-Frame-Options ===
        # Prevence clickjacking
        # SAMEORIGIN = Pouze stejná doména může framovat
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # === X-XSS-Protection ===
        # Zapne XSS filtr v prohlížeči
        # mode=block = Blokuj stránku místo sanitizace
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # === Strict-Transport-Security (HSTS) ===
        # Vynucuje HTTPS (pouze pokud běžíme na HTTPS)
        if app.config.get('PREFERRED_URL_SCHEME') == 'https' or not app.debug:
            # max-age=31536000 = 1 rok
            # includeSubDomains = Platí i pro subdomény
            response.headers['Strict-Transport-Security'] = \
                'max-age=31536000; includeSubDomains'
        
        # === Content-Security-Policy (CSP) ===
        # Definuje, odkud může stránka načítat zdroje
        
        if not app.debug:
            # Produkční CSP (přísnější)
            csp_policy = "; ".join([
                "default-src 'self'",  # Výchozí: pouze naše doména
                "script-src 'self' 'unsafe-inline'",  # JS: naše + inline
                "style-src 'self' 'unsafe-inline'",  # CSS: naše + inline
                "img-src 'self' data:",  # Obrázky: naše + data URIs
                "font-src 'self'",  # Fonty: pouze naše
                "connect-src 'self'",  # AJAX: pouze naše API
                "frame-ancestors 'self'",  # Kdo nás může framovat
                "base-uri 'self'",  # <base> tag
                "form-action 'self'",  # Kam mohou formuláře submitovat
            ])
        else:
            # Development CSP (volnější pro debugging)
            csp_policy = "; ".join([
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # unsafe-eval pro dev tools
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data:",
            ])
        
        response.headers['Content-Security-Policy'] = csp_policy
        
        # === Referrer-Policy ===
        # Kontroluje, kolik informací se posílá v Referer hlavičce
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # === Permissions-Policy (dříve Feature-Policy) ===
        # Zakazuje nebezpečné browser features
        permissions_policy = ", ".join([
            "geolocation=()",  # Zakázat geolokaci
            "microphone=()",  # Zakázat mikrofon
            "camera=()",  # Zakázat kameru
            "payment=()",  # Zakázat Payment API
        ])
        response.headers['Permissions-Policy'] = permissions_policy
        
        return response
    
    app.logger.info("Bezpečnostní HTTP hlavičky aktivovány")


def init_session_security(app: Flask) -> None:
    """
    Nastaví bezpečnou konfiguraci session cookies.
    """
    
    # === Session Cookie Security ===
    if not app.debug:
        # HTTPS only (produkce)
        app.config['SESSION_COOKIE_SECURE'] = True
    else:
        # HTTP OK (development)
        app.config['SESSION_COOKIE_SECURE'] = False
    
    # HttpOnly = JavaScript nemůže číst cookie (ochrana proti XSS)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # SameSite = Ochrana proti CSRF
    # Lax = Cookie se posílá při top-level navigaci (kliknutí na link)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Lifetime session
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    
    app.logger.info("Session security nakonfigurována")
