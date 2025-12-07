"""
Compute Engine model - represents a GCE instance
Phase 1: Metadata and state management only (no Docker logic)
Phase 5: Networking system (IP allocation, firewall rules)
"""
import time
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
from app.factory import db
from app.logging import log_formatter_stage


# Machine Type definitions (static catalog)
MACHINE_TYPES = {
    # General Purpose - E2 Series
    "e2-micro": {"cpus": 0.25, "memory_mb": 1024, "description": "0.25 vCPU, 1 GB RAM"},
    "e2-small": {"cpus": 0.5, "memory_mb": 2048, "description": "0.5 vCPU, 2 GB RAM"},
    "e2-medium": {"cpus": 1, "memory_mb": 4096, "description": "1 vCPU, 4 GB RAM"},
    "e2-standard-2": {"cpus": 2, "memory_mb": 8192, "description": "2 vCPUs, 8 GB RAM"},
    "e2-standard-4": {"cpus": 4, "memory_mb": 16384, "description": "4 vCPUs, 16 GB RAM"},
    "e2-standard-8": {"cpus": 8, "memory_mb": 32768, "description": "8 vCPUs, 32 GB RAM"},
    
    # General Purpose - N1 Series
    "n1-standard-1": {"cpus": 1, "memory_mb": 3840, "description": "1 vCPU, 3.75 GB RAM"},
    "n1-standard-2": {"cpus": 2, "memory_mb": 7680, "description": "2 vCPUs, 7.5 GB RAM"},
    "n1-standard-4": {"cpus": 4, "memory_mb": 15360, "description": "4 vCPUs, 15 GB RAM"},
    "n1-standard-8": {"cpus": 8, "memory_mb": 30720, "description": "8 vCPUs, 30 GB RAM"},
    
    # General Purpose - N2 Series
    "n2-standard-2": {"cpus": 2, "memory_mb": 8192, "description": "2 vCPUs, 8 GB RAM"},
    "n2-standard-4": {"cpus": 4, "memory_mb": 16384, "description": "4 vCPUs, 16 GB RAM"},
    "n2-standard-8": {"cpus": 8, "memory_mb": 32768, "description": "8 vCPUs, 32 GB RAM"},
}

# Instance statuses matching GCE lifecycle (Phase 2)
class InstanceStatus:
    """GCE Instance status constants - aligned with Google Compute Engine"""
    PROVISIONING = "PROVISIONING"  # Initial creation state
    STAGING = "STAGING"            # Preparing instance
    RUNNING = "RUNNING"             # Instance is running
    STOPPING = "STOPPING"           # Instance is stopping
    TERMINATED = "TERMINATED"       # Instance is stopped/terminated
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        PROVISIONING: [STAGING],
        STAGING: [RUNNING],
        RUNNING: [STOPPING],
        STOPPING: [TERMINATED],
        TERMINATED: [STAGING],  # For restart
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])


class Instance(db.Model):
    """Compute Engine Instance model"""
    __tablename__ = "compute_instances"
    
    # Core fields
    id = db.Column(db.String(36), primary_key=True)  # UUID
    name = db.Column(db.String(63), nullable=False)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"), nullable=False)
    zone = db.Column(db.String(50), nullable=False)  # e.g., "us-central1-a"
    
    # Machine configuration
    machine_type = db.Column(db.String(50), nullable=False)  # e.g., "e2-medium"
    
    # Status and lifecycle
    status = db.Column(db.String(20), default=InstanceStatus.PROVISIONING, nullable=False)
    status_message = db.Column(db.String(255), default="")
    
    # Container tracking (for future Docker integration)
    container_id = db.Column(db.String(64), nullable=True)  # Docker container ID (Phase 2)
    
    # Timestamps
    creation_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_start_timestamp = db.Column(db.DateTime, nullable=True)
    last_stop_timestamp = db.Column(db.DateTime, nullable=True)
    
    # Metadata and configuration (JSON)
    instance_metadata = db.Column(JSON, default=dict)  # User-defined metadata (renamed to avoid SQLAlchemy conflict)
    labels = db.Column(JSON, default=dict)  # User-defined labels
    tags = db.Column(JSON, default=list)  # Network tags
    
    # Network configuration (Phase 5: Networking system)
    internal_ip = db.Column(db.String(15), nullable=True)  # Internal IP (10.0.X.Y)
    external_ip = db.Column(db.String(15), nullable=True)  # External IP (203.0.113.X)
    firewall_rules = db.Column(JSON, default=list)  # Firewall rules applied to this instance
    network_interfaces = db.Column(JSON, default=list)  # List of network interfaces
    
    # Disk configuration (Phase 1: Metadata only, Phase 2: Actual volumes)
    disks = db.Column(JSON, default=list)  # List of attached disks
    
    # Indexes and constraints
    __table_args__ = (
        db.Index("idx_instances_project", "project_id"),
        db.Index("idx_instances_zone", "zone"),
        db.Index("idx_instances_status", "status"),
        db.UniqueConstraint("project_id", "zone", "name", name="instances_project_zone_name_unique"),
    )
    
    def __repr__(self) -> str:
        return f"<Instance {self.name} ({self.status})>"
    
    def _build_network_interfaces(self) -> list:
        """
        Build network interfaces array for GCE API response (Phase 5)
        Includes internal IP and external IP (if allocated)
        """
        if not self.internal_ip:
            # No networking configured yet
            return []
        
        interface = {
            "kind": "compute#networkInterface",
            "network": f"projects/{self.project_id}/global/networks/default",
            "subnetwork": f"projects/{self.project_id}/regions/{self.zone.rsplit('-', 1)[0]}/subnetworks/default",
            "networkIP": self.internal_ip,
            "name": "nic0",
            "fingerprint": "placeholder",
        }
        
        # Add external IP (access config) if allocated
        if self.external_ip:
            interface["accessConfigs"] = [{
                "kind": "compute#accessConfig",
                "type": "ONE_TO_ONE_NAT",
                "name": "External NAT",
                "natIP": self.external_ip,
                "networkTier": "PREMIUM",
            }]
        else:
            interface["accessConfigs"] = []
        
        return [interface]
    
    def get_machine_type_info(self) -> dict:
        """Get machine type specifications"""
        return MACHINE_TYPES.get(self.machine_type, {
            "cpus": 1,
            "memory_mb": 3840,
            "description": "Unknown machine type"
        })
    
    def to_dict(self) -> dict:
        """
        Convert to GCE-style JSON format
        Follows GCP Compute Engine API v1 instance resource format
        """
        start_time = time.time()
        
        log_formatter_stage(
            message="Model to_dict serialization starting",
            details={
                "model": "Instance",
                "instance_id": self.id,
                "instance_name": self.name,
            }
        )
        
        machine_info = self.get_machine_type_info()
        
        # Build GCE-compatible response
        instance_dict = {
            "kind": "compute#instance",
            "id": self.id,
            "creationTimestamp": self.creation_timestamp.isoformat() + "Z",
            "name": self.name,
            "zone": f"projects/{self.project_id}/zones/{self.zone}",
            "machineType": f"projects/{self.project_id}/zones/{self.zone}/machineTypes/{self.machine_type}",
            "status": self.status,
            "statusMessage": self.status_message,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{self.zone}/instances/{self.name}",
            
            # Metadata
            "metadata": {
                "kind": "compute#metadata",
                "items": [{"key": k, "value": v} for k, v in (self.instance_metadata or {}).items()]
            },
            
            # Labels
            "labels": self.labels or {},
            
            # Tags
            "tags": {
                "items": self.tags or [],
                "fingerprint": "placeholder"
            },
            
            # Network interfaces (Phase 5: Include IP allocation)
            "networkInterfaces": self._build_network_interfaces(),
            
            # Disks (empty list for Phase 1)
            "disks": self.disks or [],
            
            # Scheduling (basic defaults)
            "scheduling": {
                "onHostMaintenance": "MIGRATE",
                "automaticRestart": True,
                "preemptible": False
            },
            
            # Service accounts (empty for Phase 1)
            "serviceAccounts": [],
            
            # Machine type details (convenience fields)
            "cpuPlatform": "Intel Haswell",
            "guestAccelerators": [],
        }
        
        # Add start timestamp if available
        if self.last_start_timestamp:
            instance_dict["lastStartTimestamp"] = self.last_start_timestamp.isoformat() + "Z"
        
        # Add stop timestamp if available
        if self.last_stop_timestamp:
            instance_dict["lastStopTimestamp"] = self.last_stop_timestamp.isoformat() + "Z"
        
        # Add container ID if available (internal field, not part of GCE API)
        if self.container_id:
            instance_dict["_emulator_container_id"] = self.container_id
        
        duration_ms = (time.time() - start_time) * 1000
        log_formatter_stage(
            message="Model to_dict serialization completed",
            duration_ms=duration_ms,
            details={
                "instance_id": self.id,
                "instance_name": self.name,
                "status": self.status,
            }
        )
        
        return instance_dict
    
    def to_summary_dict(self) -> dict:
        """Convert to lightweight summary format for list operations"""
        return {
            "id": self.id,
            "name": self.name,
            "zone": self.zone,
            "machineType": self.machine_type,
            "status": self.status,
            "creationTimestamp": self.creation_timestamp.isoformat() + "Z",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/zones/{self.zone}/instances/{self.name}",
        }


class MachineType:
    """
    Machine Type helper class (static data, not a database model)
    Provides machine type catalog and validation
    """
    
    @staticmethod
    def get_all() -> dict:
        """Get all available machine types"""
        return MACHINE_TYPES
    
    @staticmethod
    def get(machine_type: str) -> dict:
        """Get specific machine type details"""
        return MACHINE_TYPES.get(machine_type)
    
    @staticmethod
    def is_valid(machine_type: str) -> bool:
        """Check if machine type exists"""
        return machine_type in MACHINE_TYPES
    
    @staticmethod
    def to_gce_format(machine_type: str, project_id: str, zone: str) -> dict:
        """
        Convert machine type to GCE API format
        
        Returns:
            GCE-style machine type resource
        """
        if machine_type not in MACHINE_TYPES:
            return None
        
        info = MACHINE_TYPES[machine_type]
        
        return {
            "kind": "compute#machineType",
            "id": machine_type,
            "name": machine_type,
            "description": info["description"],
            "guestCpus": info["cpus"],
            "memoryMb": info["memory_mb"],
            "zone": f"projects/{project_id}/zones/{zone}",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/machineTypes/{machine_type}",
            "maximumPersistentDisks": 16,
            "maximumPersistentDisksSizeGb": "65536",
        }


class NetworkAllocation(db.Model):
    """
    Network IP allocation tracker (Phase 5)
    Maintains counters for internal and external IP allocation
    """
    __tablename__ = "network_allocations"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"), nullable=False, unique=True)
    
    # IP allocation counters
    internal_counter = db.Column(db.Integer, default=1, nullable=False)  # Starts at 1 for 10.0.0.1
    external_counter = db.Column(db.Integer, default=10, nullable=False)  # Starts at 10 for 203.0.113.10
    
    # Track allocated IPs (for reference, not strictly enforced)
    allocated_internal_ips = db.Column(JSON, default=list)  # List of allocated internal IPs
    allocated_external_ips = db.Column(JSON, default=list)  # List of allocated external IPs
    
    def __repr__(self) -> str:
        return f"<NetworkAllocation project={self.project_id} internal={self.internal_counter} external={self.external_counter}>"
    
    def allocate_internal_ip(self) -> str:
        """
        Allocate next internal IP from 10.0.0.0/16 pool
        Format: 10.0.X.Y where X.Y = counter value
        """
        counter = self.internal_counter
        
        # Convert counter to IP octets (10.0.X.Y)
        # Counter 1 -> 10.0.0.1, Counter 256 -> 10.0.1.0, etc.
        octet_3 = (counter // 256) % 256
        octet_4 = counter % 256
        
        ip = f"10.0.{octet_3}.{octet_4}"
        
        # Increment counter
        self.internal_counter += 1
        
        # Track allocation
        if self.allocated_internal_ips is None:
            self.allocated_internal_ips = []
        self.allocated_internal_ips.append(ip)
        
        return ip
    
    def allocate_external_ip(self) -> str:
        """
        Allocate next external IP from pseudo-public pool
        Format: 203.0.113.X where X = counter value
        Uses TEST-NET-3 (RFC 5737) range
        """
        counter = self.external_counter
        
        # Simple single-octet allocation for simplicity
        # 203.0.113.X where X = counter
        ip = f"203.0.113.{counter % 256}"
        
        # Increment counter
        self.external_counter += 1
        
        # Track allocation
        if self.allocated_external_ips is None:
            self.allocated_external_ips = []
        self.allocated_external_ips.append(ip)
        
        return ip


class FirewallRule(db.Model):
    """
    Firewall Rule model (Phase 5)
    Simple allow/deny rules for ingress/egress traffic
    Metadata-only, no actual packet filtering
    """
    __tablename__ = "firewall_rules"
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    name = db.Column(db.String(63), nullable=False)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"), nullable=False)
    
    # Rule configuration
    direction = db.Column(db.String(10), nullable=False)  # INGRESS or EGRESS
    protocol = db.Column(db.String(10), nullable=False)  # tcp, udp, icmp, etc.
    port = db.Column(db.Integer, nullable=True)  # Port number (optional, for tcp/udp)
    action = db.Column(db.String(10), nullable=False, default="ALLOW")  # ALLOW or DENY
    
    # Priority (lower number = higher priority)
    priority = db.Column(db.Integer, default=1000, nullable=False)
    
    # Source/destination (simplified - just CIDR ranges)
    source_ranges = db.Column(JSON, default=lambda: ["0.0.0.0/0"])  # For INGRESS
    destination_ranges = db.Column(JSON, default=lambda: ["0.0.0.0/0"])  # For EGRESS
    
    # Target (which instances this applies to)
    target_tags = db.Column(JSON, default=list)  # Apply to instances with these tags
    
    # Metadata
    description = db.Column(db.String(255), nullable=True)
    creation_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Indexes and constraints
    __table_args__ = (
        db.Index("idx_firewall_project", "project_id"),
        db.UniqueConstraint("project_id", "name", name="firewall_project_name_unique"),
    )
    
    def __repr__(self) -> str:
        return f"<FirewallRule {self.name} {self.direction} {self.protocol}:{self.port} {self.action}>"
    
    def to_dict(self) -> dict:
        """Convert to GCE-style JSON format"""
        rule_dict = {
            "kind": "compute#firewall",
            "id": self.id,
            "creationTimestamp": self.creation_timestamp.isoformat() + "Z",
            "name": self.name,
            "description": self.description or "",
            "network": f"projects/{self.project_id}/global/networks/default",
            "priority": self.priority,
            "direction": self.direction,
            "disabled": False,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{self.project_id}/global/firewalls/{self.name}",
        }
        
        # Add allowed/denied rules based on action
        if self.action == "ALLOW":
            rule_dict["allowed"] = [{
                "IPProtocol": self.protocol,
            }]
            if self.port:
                rule_dict["allowed"][0]["ports"] = [str(self.port)]
        else:  # DENY
            rule_dict["denied"] = [{
                "IPProtocol": self.protocol,
            }]
            if self.port:
                rule_dict["denied"][0]["ports"] = [str(self.port)]
        
        # Add source/destination ranges
        if self.direction == "INGRESS":
            rule_dict["sourceRanges"] = self.source_ranges or ["0.0.0.0/0"]
        else:  # EGRESS
            rule_dict["destinationRanges"] = self.destination_ranges or ["0.0.0.0/0"]
        
        # Add target tags
        if self.target_tags:
            rule_dict["targetTags"] = self.target_tags
        
        return rule_dict
