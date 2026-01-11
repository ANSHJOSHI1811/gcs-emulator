"""
PHASE 1: Compute Instance Model
Represents a virtual machine instance backed by Docker containers
"""
from datetime import datetime
from app.factory import db
import uuid
import json


class Instance(db.Model):
    """
    Instance model for PHASE 1 - Basic lifecycle
    State machine: pending → running → stopping → stopped → terminated
    """
    __tablename__ = 'instances'
    
    # Primary identifiers
    id = db.Column(db.String(36), primary_key=True)  # UUID format
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.String(255), nullable=False, default='test-project')
    
    # GCP Compute API v1 fields
    zone = db.Column(db.String(100), default='us-central1-a')
    machine_type = db.Column(db.String(100), default='e2-micro')  # Machine type name (not full URL)
    
    # Phase 2: Metadata and Labels support
    metadata_items = db.Column(db.Text, default='{}')  # JSON string of key-value pairs (renamed from 'metadata' - SQLAlchemy reserved)
    labels = db.Column(db.Text, default='{}')  # JSON string of key-value pairs
    description = db.Column(db.Text, nullable=True)  # Optional description
    
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
            'project_id': self.project_id,
            'image': self.image,
            'cpu': self.cpu,
            'memory_mb': self.memory_mb,
            'container_id': self.container_id,
            'state': self.state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_gcp_dict(self):
        """
        Convert to GCP Compute Engine Instance format
        https://cloud.google.com/compute/docs/reference/rest/v1/instances
        """
        # Map internal state to GCP status
        status_map = {
            'pending': 'PROVISIONING',
            'running': 'RUNNING',
            'stopping': 'STOPPING',
            'stopped': 'TERMINATED',
            'terminated': 'TERMINATED'
        }
        
        zone = self.zone or 'us-central1-a'
        machine_type = self.machine_type or 'e2-micro'
        
        # Generate numeric ID (GCP uses strings but they're numeric)
        numeric_id = str(hash(self.id) % (10 ** 16))
        
        # RFC 3339 timestamp
        creation_timestamp = self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Parse metadata from JSON string
        try:
            metadata_dict = json.loads(self.metadata_items or '{}')
        except (json.JSONDecodeError, TypeError):
            metadata_dict = {}
        
        # Build metadata items array (GCP format)
        metadata_items = []
        # Add emulator defaults
        metadata_items.append({"key": "emulator", "value": "true"})
        metadata_items.append({"key": "docker_image", "value": self.image})
        metadata_items.append({"key": "cpu_count", "value": str(self.cpu)})
        metadata_items.append({"key": "memory_mb", "value": str(self.memory_mb)})
        # Add user-defined metadata
        for key, value in metadata_dict.items():
            metadata_items.append({"key": key, "value": str(value)})
        
        # Parse labels from JSON string
        try:
            labels_dict = json.loads(self.labels or '{}')
        except (json.JSONDecodeError, TypeError):
            labels_dict = {}
        
        # Determine description
        instance_description = self.description or f"Emulated instance backed by Docker ({self.image})"
        
        return {
            "kind": "compute#instance",
            "id": numeric_id,
            "creationTimestamp": creation_timestamp,
            "name": self.name,
            "description": instance_description,
            "tags": {
                "items": [],
                "fingerprint": "42WmSpB8rSM="
            },
            "machineType": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{zone}/machineTypes/{machine_type}",
            "status": status_map.get(self.state, 'TERMINATED'),
            "zone": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{zone}",
            "canIpForward": False,
            "networkInterfaces": [
                {
                    "kind": "compute#networkInterface",
                    "network": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/global/networks/default",
                    "subnetwork": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/regions/us-central1/subnetworks/default",
                    "networkIP": "10.128.0.2",
                    "name": "nic0",
                    "accessConfigs": [
                        {
                            "kind": "compute#accessConfig",
                            "type": "ONE_TO_ONE_NAT",
                            "name": "External NAT",
                            "natIP": "34.172.123.45",
                            "networkTier": "PREMIUM"
                        }
                    ],
                    "fingerprint": "QWxhZGRpbjpvc"
                }
            ],
            "disks": [
                {
                    "kind": "compute#attachedDisk",
                    "type": "PERSISTENT",
                    "mode": "READ_WRITE",
                    "source": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{zone}/disks/{self.name}",
                    "deviceName": self.name,
                    "index": 0,
                    "boot": True,
                    "autoDelete": True,
                    "licenses": [
                        "https://www.googleapis.com/compute/v1/projects/debian-cloud/global/licenses/debian-11-bullseye"
                    ],
                    "interface": "SCSI",
                    "guestOsFeatures": [
                        {"type": "UEFI_COMPATIBLE"},
                        {"type": "VIRTIO_SCSI_MULTIQUEUE"}
                    ]
                }
            ],
            "metadata": {
                "kind": "compute#metadata",
                "fingerprint": "example123",
                "items": metadata_items
            },
            "labels": labels_dict,
            "labelFingerprint": "42WmSpB8rSM=",
            "serviceAccounts": [
                {
                    "email": f"{self.project_id}-compute@developer.gserviceaccount.com",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_only",
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring.write",
                        "https://www.googleapis.com/auth/servicecontrol",
                        "https://www.googleapis.com/auth/service.management.readonly",
                        "https://www.googleapis.com/auth/trace.append"
                    ]
                }
            ],
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{zone}/instances/{self.name}",
            "scheduling": {
                "onHostMaintenance": "MIGRATE",
                "automaticRestart": True,
                "preemptible": False
            },
            "cpuPlatform": "Intel Broadwell",
            "startRestricted": False,
            "deletionProtection": False,
            "fingerprint": "example-fingerprint"
        }
    
    def __repr__(self):
        return f"<Instance {self.id} ({self.name}) - {self.state}>"
