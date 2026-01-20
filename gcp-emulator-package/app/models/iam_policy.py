"""
IAM Policy model - IAM policies and bindings for GCP emulator
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db


class IamPolicy(db.Model):
    """IAM Policy model - stores policies for resources"""
    __tablename__ = "iam_policies"
    
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(50), nullable=False)  # project, bucket, instance
    resource_id = db.Column(db.String(255), nullable=False)  # resource identifier
    version = db.Column(db.Integer, default=1)
    bindings = db.Column(JSON, default=list)  # [{role: "...", members: ["user:...", "serviceAccount:..."]}]
    etag = db.Column(db.String(255))  # for optimistic concurrency
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('resource_type', 'resource_id', name='uix_resource'),
    )
    
    def __repr__(self) -> str:
        return f"<IamPolicy {self.resource_type}/{self.resource_id}>"
    
    def to_dict(self) -> dict:
        """Convert to GCP IAM Policy format"""
        return {
            "version": self.version,
            "bindings": self.bindings or [],
            "etag": self.etag or "",
        }
    
    def has_permission(self, member: str, permission: str) -> bool:
        """Check if member has permission through role bindings"""
        if not self.bindings:
            return False
        
        # Get role mappings for permission
        role_map = get_role_permissions()
        
        for binding in self.bindings:
            role = binding.get("role", "")
            members = binding.get("members", [])
            
            # Check if member is in binding
            if member in members or "allUsers" in members or "allAuthenticatedUsers" in members:
                # Check if role grants permission
                if role in role_map and permission in role_map[role]:
                    return True
        
        return False


class Role(db.Model):
    """Role model - predefined and custom roles"""
    __tablename__ = "roles"
    
    id = db.Column(db.String(255), primary_key=True)  # roles/storage.admin or projects/{project}/roles/custom
    name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    stage = db.Column(db.String(50), default="GA")  # GA, BETA, ALPHA
    permissions = db.Column(JSON, default=list)  # ["storage.buckets.create", "storage.objects.get"]
    is_custom = db.Column(db.Boolean, default=False)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"), nullable=True)  # for custom roles
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Role {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert to GCP API format"""
        return {
            "name": self.id,
            "title": self.title,
            "description": self.description,
            "includedPermissions": self.permissions or [],
            "stage": self.stage,
        }


def get_role_permissions() -> dict:
    """Get default role to permissions mapping (hardcoded for emulator)"""
    return {
        "roles/owner": [
            "storage.buckets.*",
            "storage.objects.*",
            "compute.instances.*",
            "iam.serviceAccounts.*",
            "iam.serviceAccountKeys.*",
            "resourcemanager.projects.*",
        ],
        "roles/editor": [
            "storage.buckets.create",
            "storage.buckets.get",
            "storage.buckets.list",
            "storage.buckets.update",
            "storage.objects.*",
            "compute.instances.*",
        ],
        "roles/viewer": [
            "storage.buckets.get",
            "storage.buckets.list",
            "storage.objects.get",
            "storage.objects.list",
            "compute.instances.get",
            "compute.instances.list",
        ],
        "roles/storage.admin": [
            "storage.buckets.*",
            "storage.objects.*",
        ],
        "roles/storage.objectAdmin": [
            "storage.objects.*",
        ],
        "roles/storage.objectViewer": [
            "storage.objects.get",
            "storage.objects.list",
        ],
        "roles/compute.admin": [
            "compute.instances.*",
            "compute.zones.*",
            "compute.machineTypes.*",
        ],
        "roles/compute.instanceAdmin": [
            "compute.instances.*",
        ],
    }
