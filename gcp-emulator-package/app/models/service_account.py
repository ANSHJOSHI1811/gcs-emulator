"""
Service Account model - represents a GCP service account
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db
import secrets


class ServiceAccount(db.Model):
    """Service Account model for IAM"""
    __tablename__ = "service_accounts"
    
    # Unique identifier (email format: service-account-name@project-id.iam.gserviceaccount.com)
    email = db.Column(db.String(255), primary_key=True)
    
    # Account properties
    project_id = db.Column(db.String(63), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)  # Human-readable name
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Unique numeric ID
    unique_id = db.Column(db.String(21), unique=True, nullable=False)
    
    # OAuth2 configuration
    oauth2_client_id = db.Column(db.String(21))
    
    # Status
    disabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    meta = db.Column(JSON, default=dict)
    
    # Relationships
    keys = db.relationship("ServiceAccountKey", backref="service_account", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<ServiceAccount {self.email}>"
    
    @staticmethod
    def generate_unique_id() -> str:
        """Generate a unique numeric ID (21 digits)"""
        return str(secrets.randbits(64))[:21]
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching GCP API format"""
        return {
            "name": f"projects/{self.project_id}/serviceAccounts/{self.email}",
            "projectId": self.project_id,
            "uniqueId": self.unique_id,
            "email": self.email,
            "displayName": self.display_name,
            "description": self.description,
            "oauth2ClientId": self.oauth2_client_id,
            "disabled": self.disabled,
            "etag": self._compute_etag(),
        }
    
    def _compute_etag(self) -> str:
        """Compute ETag for versioning"""
        import hashlib
        data = f"{self.email}{self.updated_at.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()


class ServiceAccountKey(db.Model):
    """Service Account Key model"""
    __tablename__ = "service_account_keys"
    
    # Key identifier
    id = db.Column(db.String(255), primary_key=True)  # Format: projects/{PROJECT}/serviceAccounts/{EMAIL}/keys/{KEY_ID}
    
    # Foreign key
    service_account_email = db.Column(db.String(255), db.ForeignKey('service_accounts.email'), nullable=False)
    
    # Key properties
    key_algorithm = db.Column(db.String(50), default="KEY_ALG_RSA_2048")
    key_origin = db.Column(db.String(50), default="GOOGLE_PROVIDED")
    key_type = db.Column(db.String(50), default="USER_MANAGED")
    
    # Private key data (encrypted in production)
    private_key_data = db.Column(db.Text)
    public_key_data = db.Column(db.Text)
    
    # Status
    disabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    valid_after_time = db.Column(db.DateTime, default=datetime.utcnow)
    valid_before_time = db.Column(db.DateTime)  # Expiration
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ServiceAccountKey {self.id}>"
    
    def to_dict(self, include_private_key: bool = False) -> dict:
        """Convert to dictionary matching GCP API format"""
        result = {
            "name": self.id,
            "keyAlgorithm": self.key_algorithm,
            "keyOrigin": self.key_origin,
            "keyType": self.key_type,
            "validAfterTime": self.valid_after_time.isoformat() + "Z",
            "validBeforeTime": self.valid_before_time.isoformat() + "Z" if self.valid_before_time else None,
            "disabled": self.disabled,
        }
        
        if include_private_key and self.private_key_data:
            result["privateKeyData"] = self.private_key_data
            result["privateKeyType"] = "TYPE_GOOGLE_CREDENTIALS_FILE"
        
        return result
