"""
Lifecycle Rule Model - Phase 4

Basic lifecycle management (Delete/Archive actions).
"""
from app.factory import db
from datetime import datetime
import uuid


class LifecycleRule(db.Model):
    """Lifecycle rule model"""
    __tablename__ = "lifecycle_rules"
    
    rule_id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    bucket_id = db.Column(db.String(63), db.ForeignKey("buckets.id", ondelete="CASCADE"), nullable=False, index=True)
    action = db.Column(db.String(20), nullable=False)  # Delete or Archive
    age_days = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert rule to dictionary"""
        return {
            "ruleId": self.rule_id,
            "bucketName": self.bucket_name,
            "action": self.action,
            "ageDays": self.age_days,
            "createdAt": self.created_at.isoformat() + "Z" if self.created_at else None
        }
