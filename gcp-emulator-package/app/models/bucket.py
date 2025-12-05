"""
Bucket model - represents a GCS bucket
"""
import time
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db
from app.logging import log_formatter_stage


class Bucket(db.Model):
    """Bucket model"""
    __tablename__ = "buckets"
    
    id = db.Column(db.String(63), primary_key=True)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"), nullable=False)
    name = db.Column(db.String(63), unique=True, nullable=False)
    location = db.Column(db.String(50), default="US")
    storage_class = db.Column(db.String(50), default="STANDARD")
    versioning_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = db.Column(JSON, default=dict)
    
    # Relationships
    objects = db.relationship("Object", backref="bucket", lazy=True, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        db.Index("idx_buckets_project", "project_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Bucket {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        start_time = time.time()
        
        log_formatter_stage(
            message="Model to_dict serialization starting",
            details={
                "model": "Bucket",
                "bucket_id": self.id,
                "bucket_name": self.name,
                "operation": "model_to_dict"
            }
        )
        
        result = {
            "id": self.id,
            "name": self.name,
            "projectNumber": self.project_id,
            "location": self.location,
            "storageClass": self.storage_class,
            "versioning": {
                "enabled": self.versioning_enabled
            },
            "timeCreated": self.created_at.isoformat() + "Z",
            "updated": self.updated_at.isoformat() + "Z",
        }
        
        duration_ms = (time.time() - start_time) * 1000
        log_formatter_stage(
            message="Model to_dict serialization completed",
            duration_ms=duration_ms,
            details={
                "model": "Bucket",
                "fields_serialized": len(result),
                "gcs_api_compliant": True,
                "includes_timestamps": True
            }
        )
        
        return result
