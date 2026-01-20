"""
Operation Model

Tracks long-running operations for GCP API compatibility.
Terraform polls these to check operation status.
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.factory import db


class Operation(db.Model):
    """Operation model for tracking async operations"""
    __tablename__ = 'operations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False, unique=True)
    operation_type = db.Column(db.String(50), nullable=False)  # insert, delete, update, patch
    status = db.Column(db.String(20), default='DONE')  # PENDING, RUNNING, DONE, FAILED
    progress = db.Column(db.Integer, default=100)
    target_link = db.Column(db.Text)
    target_id = db.Column(db.String(255))
    project_id = db.Column(db.String(255), nullable=False)
    region = db.Column(db.String(50))  # For regional operations
    zone = db.Column(db.String(50))  # For zonal operations
    error_message = db.Column(db.Text)
    insert_time = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to GCP API format"""
        result = {
            'kind': 'compute#operation',
            'id': str(self.id),
            'name': self.name,
            'operationType': self.operation_type,
            'status': self.status,
            'progress': self.progress,
            'insertTime': self.insert_time.isoformat() + 'Z',
            'selfLink': self.self_link
        }
        
        if self.target_link:
            result['targetLink'] = self.target_link
            
        if self.target_id:
            result['targetId'] = self.target_id
            
        if self.start_time:
            result['startTime'] = self.start_time.isoformat() + 'Z'
            
        if self.end_time and self.status == 'DONE':
            result['endTime'] = self.end_time.isoformat() + 'Z'
            
        if self.error_message:
            result['error'] = {
                'errors': [{
                    'code': 'OPERATION_FAILED',
                    'message': self.error_message
                }]
            }
        
        # Add user if needed
        result['user'] = 'user@example.com'
        
        return result
    
    @property
    def self_link(self):
        """Generate selfLink based on scope"""
        base = f"http://127.0.0.1:8080/compute/v1/projects/{self.project_id}"
        
        if self.zone:
            return f"{base}/zones/{self.zone}/operations/{self.name}"
        elif self.region:
            return f"{base}/regions/{self.region}/operations/{self.name}"
        else:
            return f"{base}/global/operations/{self.name}"
