"""
IAM Policy models - represents IAM policies and bindings
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from app.factory import db


class IAMPolicy(db.Model):
    """IAM Policy model - represents a policy attached to a resource"""
    __tablename__ = "iam_policies"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Resource identifier (e.g., projects/my-project, projects/my-project/buckets/my-bucket)
    resource_name = db.Column(db.String(500), unique=True, nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=False)  # project, bucket, etc.
    
    # Policy version (for compatibility with different IAM versions)
    version = db.Column(db.Integer, default=1)
    
    # ETag for optimistic concurrency control
    etag = db.Column(db.String(64))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bindings = db.relationship("IAMBinding", backref="policy", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<IAMPolicy {self.resource_name}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching GCP API format"""
        return {
            "version": self.version,
            "bindings": [binding.to_dict() for binding in self.bindings],
            "etag": self.etag or self._compute_etag(),
        }
    
    def _compute_etag(self) -> str:
        """Compute ETag for versioning"""
        import hashlib
        data = f"{self.resource_name}{self.updated_at.isoformat()}{len(self.bindings)}"
        return hashlib.md5(data.encode()).hexdigest()


class IAMBinding(db.Model):
    """IAM Binding model - represents a role binding to members"""
    __tablename__ = "iam_bindings"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to policy
    policy_id = db.Column(db.Integer, db.ForeignKey('iam_policies.id'), nullable=False)
    
    # Role (e.g., roles/storage.objectViewer, roles/owner)
    role = db.Column(db.String(255), nullable=False)
    
    # Members (stored as PostgreSQL array)
    # Format: ["user:user@example.com", "serviceAccount:sa@project.iam.gserviceaccount.com", "allUsers"]
    members = db.Column(ARRAY(db.String(500)), default=list, nullable=False)
    
    # Condition (optional IAM condition)
    condition = db.Column(JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<IAMBinding {self.role} with {len(self.members)} members>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching GCP API format"""
        result = {
            "role": self.role,
            "members": self.members or [],
        }
        
        if self.condition:
            result["condition"] = self.condition
        
        return result


class Role(db.Model):
    """Role model - represents a custom or predefined IAM role"""
    __tablename__ = "iam_roles"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Role name (e.g., roles/storage.objectViewer or projects/my-project/roles/customRole)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Role properties
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    stage = db.Column(db.String(50), default="GA")  # GA, BETA, ALPHA, DEPRECATED
    
    # Role type
    is_custom = db.Column(db.Boolean, default=False, nullable=False)
    project_id = db.Column(db.String(63), db.ForeignKey('projects.id'))
    
    # Permissions (stored as PostgreSQL array)
    # Format: ["storage.objects.get", "storage.objects.list"]
    included_permissions = db.Column(ARRAY(db.String(255)), default=list, nullable=False)
    
    # Deleted flag (for soft delete)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ETag for versioning
    etag = db.Column(db.String(64))
    
    def __repr__(self) -> str:
        return f"<Role {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching GCP API format"""
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "includedPermissions": self.included_permissions or [],
            "stage": self.stage,
            "deleted": self.deleted,
            "etag": self.etag or self._compute_etag(),
        }
    
    def _compute_etag(self) -> str:
        """Compute ETag for versioning"""
        import hashlib
        data = f"{self.name}{self.updated_at.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()
