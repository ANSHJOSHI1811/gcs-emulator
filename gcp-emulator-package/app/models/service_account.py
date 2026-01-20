"""
Service Account model - IAM service accounts for GCP emulator
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db


class ServiceAccount(db.Model):
    """Service Account model for IAM"""
    __tablename__ = "service_accounts"
    
    id = db.Column(db.String(255), primary_key=True)  # projects/{project}/serviceAccounts/{email}
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    display_name = db.Column(db.String(255))
    description = db.Column(db.Text)
    unique_id = db.Column(db.String(21), unique=True, nullable=False)  # numeric ID
    disabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    keys = db.relationship("ServiceAccountKey", backref="service_account", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<ServiceAccount {self.email}>"
    
    def to_dict(self) -> dict:
        """Convert to GCP API format"""
        return {
            "name": self.id,
            "projectId": self.project_id,
            "uniqueId": self.unique_id,
            "email": self.email,
            "displayName": self.display_name,
            "description": self.description,
            "disabled": self.disabled,
            "oauth2ClientId": self.unique_id,
        }


class ServiceAccountKey(db.Model):
    """Service Account Key model"""
    __tablename__ = "service_account_keys"
    
    id = db.Column(db.String(255), primary_key=True)  # Full resource name
    service_account_id = db.Column(db.String(255), db.ForeignKey("service_accounts.id"), nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)  # Short name
    private_key_type = db.Column(db.String(50), default="TYPE_GOOGLE_CREDENTIALS_FILE")
    key_algorithm = db.Column(db.String(50), default="KEY_ALG_RSA_2048")
    private_key_data = db.Column(db.Text)  # JSON key file content
    public_key_data = db.Column(db.Text)
    valid_after = db.Column(db.DateTime, default=datetime.utcnow)
    valid_before = db.Column(db.DateTime)
    disabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ServiceAccountKey {self.name}>"
    
    def to_dict(self, include_private=False) -> dict:
        """Convert to GCP API format"""
        result = {
            "name": self.id,
            "privateKeyType": self.private_key_type,
            "keyAlgorithm": self.key_algorithm,
            "validAfterTime": self.valid_after.isoformat() + "Z",
            "disabled": self.disabled,
        }
        if self.valid_before:
            result["validBeforeTime"] = self.valid_before.isoformat() + "Z"
        if include_private and self.private_key_data:
            result["privateKeyData"] = self.private_key_data
        if self.public_key_data:
            result["publicKeyData"] = self.public_key_data
        return result
