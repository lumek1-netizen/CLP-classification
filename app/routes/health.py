"""
Health check endpoints pro monitoring.
"""
from flask import Blueprint, jsonify, current_app
from app.extensions import db, cache, limiter
from datetime import datetime
import os

health_bp = Blueprint('health', __name__)

# Vyjmi health endpoints z rate limitingu
limiter.exempt(health_bp)


@health_bp.route('/health')
def health_check():
    """
    Základní health check - rychlá kontrola dostupnosti.
    """
    try:
        # Zkontroluj databázi (jednoduchý dotaz)
        db.session.execute(db.text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
        }), 503


@health_bp.route('/health/detailed')
def detailed_health_check():
    """
    Detailní health check - kontrola všech komponent.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # === 1. DATABASE ===
    try:
        # SQLite doesn't have version() function by default in all versions, 
        # so we use a more generic query or just SELECT 1
        db.session.execute(db.text('SELECT 1'))
        health_status['checks']['database'] = {
            'status': 'healthy'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # === 2. CACHE ===
    try:
        cache.set('health_check', 'ok', timeout=5)
        value = cache.get('health_check')
        
        health_status['checks']['cache'] = {
            'status': 'healthy' if value == 'ok' else 'degraded',
            'type': current_app.config.get('CACHE_TYPE')
        }
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # === 3. DISK SPACE ===
    try:
        import shutil
        total, used, free = shutil.disk_usage('/')
        percent_used = (used / total) * 100
        
        health_status['checks']['disk'] = {
            'status': 'healthy' if percent_used < 90 else 'warning',
            'percent_used': round(percent_used, 2),
            'free_gb': round(free / (1024**3), 2)
        }
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code
