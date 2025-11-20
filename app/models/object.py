"""
Object model - represents a GCS object (file)
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db


class Object(db.Model):
    """Object (file) model"""
    __tablename__ = "objects"
    
    id = db.Column(db.String(255), primary_key=True)
    bucket_id = db.Column(db.String(63), db.ForeignKey("buckets.id"), nullable=False)
    name = db.Column(db.String(1024), nullable=False)
    size = db.Column(db.BigInteger, default=0)
    content_type = db.Column(db.String(255), default="application/octet-stream")
    md5_hash = db.Column(db.String(32))
    crc32c_hash = db.Column(db.String(44))
    file_path = db.Column(db.String(1024))
    metageneration = db.Column(db.BigInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = db.Column(JSON, default={})
    
    # Indexes
    __table_args__ = (
        db.Index("idx_objects_bucket", "bucket_id"),
        db.Index("idx_objects_name", "name"),
    )
    
    def __repr__(self) -> str:
        return f"<Object {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "bucket": self.bucket_id,
            "size": str(self.size),  # Note: returned as string per Google API
            "contentType": self.content_type,
            "md5Hash": self.md5_hash,
            "crc32c": self.crc32c_hash,
            "metageneration": str(self.metageneration),
            "timeCreated": self.created_at.isoformat() + "Z",
            "updated": self.updated_at.isoformat() + "Z",
        }
