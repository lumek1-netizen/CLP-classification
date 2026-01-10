from app.extensions import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)  # 'substance' nebo 'mixture'
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    changes = db.Column(db.JSON, nullable=True)  # JSON s rozdíly
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("audit_logs", lazy=True))

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id} by User:{self.user_id}>"
