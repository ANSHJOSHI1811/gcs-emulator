"""
Object model - represents a GCS object (file)
"""
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db


class Object(db.Model):
    """Object (file) model - stores latest version metadata"""
    __tablename__ = "objects"
    
    id = db.Column(db.String(255), primary_key=True)
    bucket_id = db.Column(db.String(63), db.ForeignKey("buckets.id"), nullable=False)
    name = db.Column(db.String(1024), nullable=False)
    generation = db.Column(db.BigInteger, default=1, nullable=False)
    size = db.Column(db.BigInteger, default=0)
    content_type = db.Column(db.String(255), default="application/octet-stream")
    md5_hash = db.Column(db.String(32))
    crc32c_hash = db.Column(db.String(44))
    file_path = db.Column(db.String(1024))
    metageneration = db.Column(db.BigInteger, default=1)
    storage_class = db.Column(db.String(50), default="STANDARD")  # Phase 4: For lifecycle Archive
    acl = db.Column(db.String(20), default="private")  # Phase 4: Minimal ACL
    is_latest = db.Column(db.Boolean, default=True, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    time_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    meta = db.Column(JSON, default=dict)
    
    # Relationship to versions
    versions = db.relationship("ObjectVersion", backref="object", lazy="dynamic", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        db.Index("idx_objects_bucket", "bucket_id"),
        db.Index("idx_objects_name", "name"),
        db.Index("idx_objects_bucket_name", "bucket_id", "name"),
    )
    
    def __repr__(self) -> str:
        return f"<Object {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary - GCS JSON API v1 format"""
        # Get the actual bucket name from the relationship
        from app.models.bucket import Bucket
        bucket = Bucket.query.filter_by(id=self.bucket_id).first()
        bucket_name = bucket.name if bucket else self.bucket_id
        
        # RFC 3339 timestamp formatting: YYYY-MM-DDTHH:MM:SS.sssZ
        time_created_rfc3339 = self.time_created.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        updated_rfc3339 = self.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        return {
            "kind": "storage#object",
            "id": f"{bucket_name}/{self.name}/{self.generation}",
            "selfLink": f"/storage/v1/b/{bucket_name}/o/{self.name}",
            "name": self.name,
            "bucket": bucket_name,
            "generation": str(self.generation),
            "metageneration": str(self.metageneration),
            "contentType": self.content_type,
            "timeCreated": time_created_rfc3339,
            "updated": updated_rfc3339,
            "size": str(self.size),
            "md5Hash": self.md5_hash,
            "crc32c": self.crc32c_hash,
        }


class ObjectVersion(db.Model):
    """ObjectVersion - stores all versions of an object"""
    __tablename__ = "object_versions"
    
    id = db.Column(db.String(255), primary_key=True)
    object_id = db.Column(db.String(255), db.ForeignKey("objects.id"), nullable=False)
    bucket_id = db.Column(db.String(63), db.ForeignKey("buckets.id"), nullable=False)
    name = db.Column(db.String(1024), nullable=False)
    generation = db.Column(db.BigInteger, nullable=False)
    metageneration = db.Column(db.BigInteger, default=1)
    size = db.Column(db.BigInteger, default=0)
    content_type = db.Column(db.String(255), default="application/octet-stream")
    md5_hash = db.Column(db.String(32))
    crc32c_hash = db.Column(db.String(44))
    file_path = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    meta = db.Column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        db.Index("idx_object_versions_bucket", "bucket_id"),
        db.Index("idx_object_versions_name", "name"),
        db.Index("idx_object_versions_generation", "bucket_id", "name", "generation"),
        db.Index("idx_object_versions_object_id", "object_id"),
        db.UniqueConstraint("bucket_id", "name", "generation", name="uq_bucket_name_generation"),
    )
    
    def __repr__(self) -> str:
        return f"<ObjectVersion {self.name} gen={self.generation}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary - GCS JSON API v1 format"""
        # Get the actual bucket name from the relationship
        from app.models.bucket import Bucket
        bucket = Bucket.query.filter_by(id=self.bucket_id).first()
        bucket_name = bucket.name if bucket else self.bucket_id
        
        # RFC 3339 timestamp formatting: YYYY-MM-DDTHH:MM:SS.sssZ
        time_created_rfc3339 = self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        updated_rfc3339 = self.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        return {
            "kind": "storage#object",
            "id": f"{bucket_name}/{self.name}/{self.generation}",
            "selfLink": f"/storage/v1/b/{bucket_name}/o/{self.name}",
            "name": self.name,
            "bucket": bucket_name,
            "generation": str(self.generation),
            "metageneration": str(self.metageneration),
            "contentType": self.content_type,
            "timeCreated": time_created_rfc3339,
            "updated": updated_rfc3339,
            "size": str(self.size),
            "md5Hash": self.md5_hash,
            "crc32c": self.crc32c_hash,
        }

