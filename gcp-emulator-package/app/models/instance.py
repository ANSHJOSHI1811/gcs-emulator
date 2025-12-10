"""
PHASE 1: Compute Instance Model
Represents a virtual machine instance backed by Docker containers
"""
from datetime import datetime
from app.factory import db
import uuid


class Instance(db.Model):
    """
    Instance model for PHASE 1 - Basic lifecycle
    State machine: pending → running → stopping → stopped → terminated
    """
    __tablename__ = 'instances'
    
    # Primary identifiers
    id = db.Column(db.String(36), primary_key=True)  # UUID format
    name = db.Column(db.String(255), nullable=False)
    
    # Instance configuration
    image = db.Column(db.String(500), nullable=False)  # Docker image name
    cpu = db.Column(db.Integer, default=1)  # Number of CPU cores
    memory_mb = db.Column(db.Integer, default=512)  # Memory in MB
    
    # Container mapping
    container_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    
    # State management (FSM: pending → running → stopping → stopped, any → terminated)
    state = db.Column(
        db.String(20), 
        nullable=False, 
        default='pending',
        index=True
    )
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert instance to simple JSON dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'image': self.image,
            'cpu': self.cpu,
            'memory_mb': self.memory_mb,
            'container_id': self.container_id,
            'state': self.state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Instance {self.id} ({self.name}) - {self.state}>"
