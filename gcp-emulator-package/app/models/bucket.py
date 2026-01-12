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
    name = db.Column(db.String(63), nullable=False)
    location = db.Column(db.String(50), default="US")
    storage_class = db.Column(db.String(50), default="STANDARD")
    versioning_enabled = db.Column(db.Boolean, default=False)
    acl = db.Column(db.String(20), default="private")  # Phase 4: Minimal ACL
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = db.Column(JSON, default=dict)
    cors = db.Column(db.Text, default=None)  # CORS configuration (JSON)
    notification_configs = db.Column(db.Text, default=None)  # Notification webhooks (JSON)
    lifecycle_config = db.Column(db.Text, default=None)  # Lifecycle rules (JSON)
    
    # Relationships
    objects = db.relationship("Object", backref="bucket", lazy=True, cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        db.Index("idx_buckets_project", "project_id"),
        db.UniqueConstraint("project_id", "name", name="buckets_project_name_unique"),
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
        
        # RFC 3339 timestamp formatting: YYYY-MM-DDTHH:MM:SS.sssZ
        time_created_rfc3339 = self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        updated_rfc3339 = self.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Generate numeric project number (hash of project_id to get consistent number)
        project_number = abs(hash(self.project_id)) % (10**12)
        
        result = {
            "id": self.name,  # GCS uses bucket name as ID in API responses
            "name": self.name,
            "projectNumber": str(project_number),
            "location": self.location,
            "storageClass": self.storage_class,
            "versioning": {
                "enabled": self.versioning_enabled
            },
            "timeCreated": time_created_rfc3339,
            "updated": updated_rfc3339,
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
