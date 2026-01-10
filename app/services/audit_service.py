from flask_login import current_user
from app.models.audit import AuditLog
from app.extensions import db
from sqlalchemy import event
import json

class AuditService:
    @staticmethod
    def log_change(entity, action, changes=None):
        """
        Vytvoří záznam do audit logu.
        """
        from app.models.substance import Substance
        from app.models.mixture import Mixture

        entity_type = None
        if isinstance(entity, Substance):
            entity_type = "substance"
        elif isinstance(entity, Mixture):
            entity_type = "mixture"
        
        if not entity_type:
            return

        user_id = None
        if current_user and current_user.is_authenticated:
            user_id = current_user.id

        log_entry = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity.id,
            action=action,
            changes=changes
        )
        db.session.add(log_entry)

    @staticmethod
    def get_object_changes(obj):
        """
        Vypočítá změny u objektu před uložením.
        """
        changes = {}
        for attr in db.inspect(obj).attrs:
            history = attr.history
            if history.has_changes():
                # history.deleted[0] je stará hodnota, history.added[0] je nová
                old_val = history.deleted[0] if history.deleted else None
                new_val = history.added[0] if history.added else None
                
                # Ignorujeme interní pole jako updated_at pokud se mění automaticky
                if attr.key in ['updated_at']:
                    continue
                    
                changes[attr.key] = {
                    "old": str(old_val) if old_val is not None else None,
                    "new": str(new_val) if new_val is not None else None
                }
        return changes

def register_audit_listeners():
    from app.models.substance import Substance
    from app.models.mixture import Mixture

    @event.listens_for(Substance, 'after_insert')
    @event.listens_for(Mixture, 'after_insert')
    def after_insert(mapper, connection, target):
        try:
            # Pro Create logujeme základní data (bez vztahů)
            initial_data = {
                k: str(v) for k, v in target.__dict__.items() 
                if not k.startswith('_') and k != 'classification_log'
            }
            AuditService.log_change(target, 'CREATE', {"initial": initial_data})
        except Exception:
            pass # Selhání logu nesmí shodit aplikaci

    @event.listens_for(Substance, 'after_update')
    @event.listens_for(Mixture, 'after_update')
    def after_update(mapper, connection, target):
        try:
            changes = AuditService.get_object_changes(target)
            if changes:
                AuditService.log_change(target, 'UPDATE', changes)
        except Exception:
            pass

    @event.listens_for(Substance, 'before_delete')
    @event.listens_for(Mixture, 'before_delete')
    def before_delete(mapper, connection, target):
        try:
            AuditService.log_change(target, 'DELETE')
        except Exception:
            pass
