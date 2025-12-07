"""
Object Event Model - Phase 4

Tracks object change events for local event notification system.
"""
from app.factory import db
from datetime import datetime, timezone


class ObjectEvent(db.Model):
    """Object change event model"""
    __tablename__ = "object_events"
    
    event_id = db.Column(db.String(255), primary_key=True)
    bucket_name = db.Column(db.String(63), nullable=False, index=True)
    object_name = db.Column(db.String(1024), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # OBJECT_FINALIZE, OBJECT_DELETE, OBJECT_METADATA_UPDATE
    generation = db.Column(db.BigInteger)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    metadata_json = db.Column(db.Text)
    delivered = db.Column(db.Boolean, default=False, index=True)
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "bucket_name": self.bucket_name,
            "object_name": self.object_name,
            "event_type": self.event_type,
            "generation": str(self.generation) if self.generation else None,
            "timestamp": self.timestamp.isoformat() + "Z" if self.timestamp else None,
            "metadata": self.metadata_json,
            "delivered": self.delivered
        }
