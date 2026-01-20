"""
GCP Compute Engine API v1 Compatibility Layer
Provides SDK-compatible REST endpoints for google-cloud-compute SDK
"""
from datetime import datetime
from app.factory import db


class ComputeOperation(db.Model):
    """
    Represents a long-running operation (LRO) for Compute Engine
    GCP Operations track async operations like insert, delete, start, stop
    """
    __tablename__ = 'compute_operations'
    
    # Operation identifiers
    id = db.Column(db.String(36), primary_key=True)  # UUID
    name = db.Column(db.String(255), nullable=False)  # Format: operation-{timestamp}
    
    # Resource context
    project_id = db.Column(db.String(255), nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    target_id = db.Column(db.String(36))  # Instance ID being operated on
    target_link = db.Column(db.String(500))  # Full resource URL
    
    # Operation properties
    operation_type = db.Column(db.String(50), nullable=False)  # insert, delete, start, stop
    status = db.Column(db.String(20), nullable=False, default='DONE')  # PENDING, RUNNING, DONE
    progress = db.Column(db.Integer, default=100)  # 0-100
    
    # Status details
    status_message = db.Column(db.String(500))
    error_code = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    
    # Timestamps
    insert_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User info
    user = db.Column(db.String(255), default='user@test-project.iam.gserviceaccount.com')
    
    def to_gcp_dict(self) -> dict:
        """
        Convert to GCP Compute Engine Operation format
        https://cloud.google.com/compute/docs/reference/rest/v1/zoneOperations
        """
        return {
            "kind": "compute#operation",
            "id": str(hash(self.id) % (10 ** 16)),  # Numeric ID
            "name": self.name,
            "zone": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{self.zone}",
            "operationType": self.operation_type,
            "targetLink": self.target_link,
            "targetId": str(hash(self.target_id) % (10 ** 16)) if self.target_id else None,
            "status": self.status,
            "progress": self.progress,
            "insertTime": self.insert_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "startTime": self.start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if self.start_time else None,
            "endTime": self.end_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if self.end_time else None,
            "user": self.user,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{self.zone}/operations/{self.name}"
        }
    
    def __repr__(self):
        return f"<ComputeOperation {self.name} - {self.status}>"
