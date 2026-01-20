"""
Compute Engine models - Instances, Zones, Machine Types
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db


class Zone(db.Model):
    """Zone model - GCP zones"""
    __tablename__ = "zones"
    
    id = db.Column(db.String(100), primary_key=True)  # us-central1-a
    name = db.Column(db.String(100), unique=True, nullable=False)
    region = db.Column(db.String(100), nullable=False)  # us-central1
    status = db.Column(db.String(50), default="UP")
    description = db.Column(db.Text)
    
    def __repr__(self) -> str:
        return f"<Zone {self.name}>"
    
    def to_dict(self, project_id="demo-project") -> dict:
        """Convert to GCP API format"""
        return {
            "id": str(abs(hash(self.name)) % (10**18)),
            "name": self.name,
            "region": f"https://www.googleapis.com/compute/v1/projects/{project_id}/regions/{self.region}",
            "status": self.status,
            "description": self.description or f"Zone {self.name}",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{self.name}",
        }


class MachineType(db.Model):
    """Machine Type model"""
    __tablename__ = "machine_types"
    
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(100), db.ForeignKey("zones.id"), nullable=False)
    guest_cpus = db.Column(db.Integer, default=1)
    memory_mb = db.Column(db.Integer, default=1024)
    description = db.Column(db.Text)
    is_shared_cpu = db.Column(db.Boolean, default=False)
    
    def __repr__(self) -> str:
        return f"<MachineType {self.name}>"
    
    def to_dict(self, project_id="demo-project") -> dict:
        """Convert to GCP API format"""
        return {
            "id": str(abs(hash(f"{self.zone}/{self.name}")) % (10**18)),
            "name": self.name,
            "zone": self.zone,
            "guestCpus": self.guest_cpus,
            "memoryMb": self.memory_mb,
            "description": self.description or f"Machine type {self.name}",
            "isSharedCpu": self.is_shared_cpu,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{self.zone}/machineTypes/{self.name}",
        }


class Instance(db.Model):
    """Compute Instance model"""
    __tablename__ = "instances"
    
    id = db.Column(db.String(255), primary_key=True)  # Unique ID
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    zone = db.Column(db.String(500), db.ForeignKey("zones.id"), nullable=False)  # Increased for URL format
    machine_type = db.Column(db.String(500), nullable=False)  # Increased for URL format
    status = db.Column(db.String(50), default="PROVISIONING")  # PROVISIONING, RUNNING, STOPPING, STOPPED, TERMINATED
    
    # Container/Docker info
    container_id = db.Column(db.String(255))  # Docker container ID
    container_name = db.Column(db.String(255))  # Docker container name
    
    # Network
    internal_ip = db.Column(db.String(15))
    external_ip = db.Column(db.String(15))
    network_url = db.Column(db.String(500))  # VPC network URL
    subnetwork_url = db.Column(db.String(500))  # Subnet URL
    network_tier = db.Column(db.String(50), default="PREMIUM")  # PREMIUM or STANDARD
    
    # Image and disk
    source_image = db.Column(db.String(500))  # Increased for URL format
    disk_size_gb = db.Column(db.Integer, default=10)
    
    # Metadata
    instance_metadata = db.Column(JSON, default=dict)
    labels = db.Column(JSON, default=dict)
    tags = db.Column(JSON, default=list)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Service account (for the instance)
    service_account_email = db.Column(db.String(255))
    service_account_scopes = db.Column(JSON, default=list)
    
    __table_args__ = (
        db.UniqueConstraint('project_id', 'zone', 'name', name='uix_instance_name'),
    )
    
    def __repr__(self) -> str:
        return f"<Instance {self.name}>"
    
    def to_dict(self, project_id="demo-project") -> dict:
        """Convert to GCP API format"""
        result = {
            "id": str(abs(hash(f"{project_id}/{self.zone}/{self.name}")) % (10**18)),
            "name": self.name,
            "zone": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{self.zone}",
            "machineType": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{self.zone}/machineTypes/{self.machine_type}",
            "status": self.status,
            "creationTimestamp": self.created_at.isoformat() + "Z",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{self.zone}/instances/{self.name}",
        }
        
        # Get network interfaces from database
        from app.models.vpc import NetworkInterface
        interfaces = NetworkInterface.query.filter_by(instance_id=self.id).order_by(NetworkInterface.nic_index).all()
        
        if interfaces:
            result["networkInterfaces"] = [iface.to_dict(project_id) for iface in interfaces]
            # Add external IP to first interface if instance has one (backward compatibility)
            if self.external_ip and result["networkInterfaces"]:
                if not result["networkInterfaces"][0].get("accessConfigs"):
                    result["networkInterfaces"][0]["accessConfigs"] = []
                result["networkInterfaces"][0]["accessConfigs"].append({
                    "natIP": self.external_ip,
                    "type": "ONE_TO_ONE_NAT",
                    "name": "External NAT"
                })
        elif self.internal_ip or self.external_ip:
            # Fallback for instances without network interface records (backward compatibility)
            result["networkInterfaces"] = [{
                "network": f"https://www.googleapis.com/compute/v1/projects/{project_id}/global/networks/default",
                "networkIP": self.internal_ip,
                "accessConfigs": [{"natIP": self.external_ip, "type": "ONE_TO_ONE_NAT", "name": "External NAT"}] if self.external_ip else []
            }]
        
        if self.source_image:
            result["disks"] = [{
                "boot": True,
                "source": self.source_image,
                "diskSizeGb": str(self.disk_size_gb),
            }]
        
        if self.instance_metadata:
            result["metadata"] = self.instance_metadata
        
        if self.labels:
            result["labels"] = self.labels
        
        if self.tags:
            result["tags"] = {"items": self.tags}
        
        if self.service_account_email:
            result["serviceAccounts"] = [{
                "email": self.service_account_email,
                "scopes": self.service_account_scopes or []
            }]
        
        # Emulator-specific fields
        result["_emulator"] = {
            "containerId": self.container_id,
            "containerName": self.container_name,
        }
        
        return result
