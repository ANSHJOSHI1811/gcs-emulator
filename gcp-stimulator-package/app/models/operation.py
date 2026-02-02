"""
Operation Model - GCP Operations tracking
"""
from app.factory import db
from datetime import datetime
import uuid


class Operation(db.Model):
    """GCP Compute Operation"""
    __tablename__ = 'operations'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='PENDING')
    progress = db.Column(db.Integer, default=0)
    target_link = db.Column(db.String(500))
    target_id = db.Column(db.String(100))
    project_id = db.Column(db.String(255), nullable=False)
    region = db.Column(db.String(100))
    zone = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    insert_time = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert to GCP API format"""
        base_url = "http://127.0.0.1:8080/compute/v1"
        project = f"projects/{self.project_id}"
        
        # Determine selfLink based on scope
        if self.zone:
            scope_path = f"{project}/zones/{self.zone}"
        elif self.region:
            scope_path = f"{project}/regions/{self.region}"
        else:
            scope_path = f"{project}/global"
        
        result = {
            "kind": "compute#operation",
            "id": str(self.id),
            "name": self.name,
            "operationType": self.operation_type,
            "targetLink": self.target_link,
            "targetId": self.target_id,
            "status": self.status,
            "user": "user@example.com",
            "progress": self.progress,
            "insertTime": self.insert_time.isoformat() + "Z" if self.insert_time else None,
            "startTime": self.start_time.isoformat() + "Z" if self.start_time else None,
            "selfLink": f"{base_url}/{scope_path}/operations/{self.name}"
        }
        
        if self.status == "DONE":
            result["endTime"] = self.end_time.isoformat() + "Z" if self.end_time else None
        
        if self.error_message:
            result["error"] = {
                "errors": [{
                    "code": "OPERATION_FAILED",
                    "message": self.error_message
                }]
            }
        
        return result
