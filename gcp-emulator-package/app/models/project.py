"""
Project model - represents a GCP project
"""
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db


class Project(db.Model):
    """Project model"""
    __tablename__ = "projects"
    
    id = db.Column(db.String(63), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(50), default="US")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    meta = db.Column(JSON, default=dict)
    
    # Relationships
    buckets = db.relationship("Bucket", backref="project", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Project {self.id}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "createdAt": self.created_at.isoformat() + "Z",
            "updatedAt": self.updated_at.isoformat() + "Z",
        }
