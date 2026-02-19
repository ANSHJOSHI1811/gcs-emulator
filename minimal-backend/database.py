"""Database models and connection"""
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean, Integer, LargeBinary, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/gcs_stimulator.db")

# For SQLite, disable connection pooling and table naming constraints
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Instance(Base):
    """VM Instance = Docker Container"""
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    project_id = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    machine_type = Column(String, nullable=False)
    status = Column(String, default="RUNNING")
    container_id = Column(String)  # Docker container ID
    container_name = Column(String)  # Docker container name
    internal_ip = Column(String)
    external_ip = Column(String)
    network_url = Column(String, default="global/networks/default")
    subnetwork_url = Column(String)
    subnet = Column(String, default="default")  # Subnet name for IP allocation
    source_image = Column(String, default="debian-11")
    disk_size_gb = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Project(Base):
    """GCP Projects"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)  # project_id
    name = Column(String, nullable=False)
    project_number = Column(Integer)
    location = Column(String, default="us-central1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    compute_api_enabled = Column(Boolean, default=True)

class Zone(Base):
    """Compute zones"""
    __tablename__ = "zones"
    
    id = Column(String, primary_key=True)  # zone name
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    status = Column(String, default="UP")
    description = Column(String)

class MachineType(Base):
    """Machine types"""
    __tablename__ = "machine_types"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    guest_cpus = Column(Integer, default=1)
    memory_mb = Column(Integer, default=1024)
    description = Column(String)

class Network(Base):
    """VPC Network = Docker Network"""
    __tablename__ = "networks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    project_id = Column(String, nullable=False)
    docker_network_name = Column(String)  # Docker network name
    auto_create_subnetworks = Column(Boolean, default=True)
    cidr_range = Column(String, default="10.128.0.0/16")  # VPC CIDR range
    creation_timestamp = Column(DateTime, default=datetime.utcnow)


class Subnet(Base):
    """Subnet within VPC Network"""
    __tablename__ = "subnets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    network = Column(String, nullable=False)  # Network name
    region = Column(String, nullable=False)
    ip_cidr_range = Column(String, nullable=False)  # e.g., "10.0.1.0/24"
    gateway_ip = Column(String)
    next_available_ip = Column(Integer, default=2)  # Start at .2 (skip .0, .1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Firewall(Base):
    """Firewall rule for VPC Network"""
    __tablename__ = "firewalls"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    network = Column(String, nullable=False)  # Network reference
    project_id = Column(String, nullable=False)
    description = Column(String)
    direction = Column(String, default="INGRESS")  # INGRESS or EGRESS
    priority = Column(Integer, default=1000)
    source_ranges = Column(JSON)  # List of source IP ranges
    destination_ranges = Column(JSON)  # List of destination IP ranges
    source_tags = Column(JSON)  # List of source tags
    target_tags = Column(JSON)  # List of target tags
    allowed = Column(JSON)  # List of {protocol, ports} dicts
    denied = Column(JSON)  # List of {protocol, ports} dicts
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Route(Base):
    """VPC Route"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    network = Column(String, nullable=False)  # Network reference
    project_id = Column(String, nullable=False)
    description = Column(String)
    dest_range = Column(String, nullable=False)  # Destination IP range
    next_hop_gateway = Column(String)  # e.g., "default-internet-gateway"
    next_hop_instance = Column(String)  # Instance name
    next_hop_ip = Column(String)  # IP address
    next_hop_network = Column(String)  # Network reference
    priority = Column(Integer, default=1000)
    tags = Column(JSON)  # List of instance tags
    created_at = Column(DateTime, default=datetime.utcnow)


class SignedUrlSession(Base):
    """Signed URL session for temporary object access"""
    __tablename__ = "signed_url_sessions"
    
    id = Column(String, primary_key=True)  # Random token
    bucket = Column(String, nullable=False)
    object_name = Column(String, nullable=False)
    method = Column(String, default="GET")
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)


class Bucket(Base):
    """Cloud Storage Bucket"""
    __tablename__ = "buckets"
    
    id = Column(String, primary_key=True)  # bucket name
    name = Column(String, nullable=False, unique=True)
    project_id = Column(String)  # Match existing column name
    location = Column(String, default="US")
    storage_class = Column(String, default="STANDARD")
    versioning_enabled = Column(Boolean, default=False)
    acl = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = Column(JSON)
    cors = Column(String)
    notification_configs = Column(String)
    lifecycle_config = Column(String)


class Object(Base):
    """Cloud Storage Object"""
    __tablename__ = "objects"
    
    id = Column(String, primary_key=True)
    bucket_id = Column(String, nullable=False)  # Match actual column
    name = Column(String, nullable=False)
    generation = Column(Integer, default=1)
    size = Column(Integer)
    content_type = Column(String)
    md5_hash = Column(String)
    crc32c_hash = Column(String)  # Match actual column name
    file_path = Column(String)  # File system path, not binary content
    metageneration = Column(Integer, default=1)
    storage_class = Column(String)
    acl = Column(String)
    is_latest = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    time_created = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta = Column(JSON)


class ServiceAccount(Base):
    """IAM Service Account"""
    __tablename__ = "service_accounts"
    
    id = Column(String, primary_key=True)  # email address
    project_id = Column(String, nullable=False)
    email = Column(String)  # duplicate of id for compatibility
    display_name = Column(String)
    description = Column(String)
    unique_id = Column(String, nullable=False, unique=True)  # numeric ID
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GKECluster(Base):
    """GKE Cluster — backed by a k3s Docker container"""
    __tablename__ = "gke_clusters"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(String, nullable=False)
    project_id     = Column(String, nullable=False)
    location       = Column(String, nullable=False)           # zone or region, e.g. us-central1-a
    status         = Column(String, default="PROVISIONING")   # PROVISIONING|RUNNING|RECONCILING|STOPPING|STOPPED|ERROR
    master_version = Column(String, default="1.28.0")
    node_count     = Column(Integer, default=3)
    machine_type   = Column(String, default="e2-medium")
    disk_size_gb   = Column(Integer, default=100)
    network        = Column(String, default="default")
    subnetwork     = Column(String, default="default")
    container_id   = Column(String)                           # Docker container ID of k3s control plane
    endpoint       = Column(String)                           # Bridge IP of k3s container
    kubeconfig     = Column(String)                           # Raw kubeconfig YAML
    description    = Column(String)
    # ── GCP-aligned fields (Sprint 2) ──
    cluster_type          = Column(String, default="STANDARD")          # STANDARD | AUTOPILOT
    release_channel       = Column(String, default="REGULAR")           # RAPID | REGULAR | STABLE | NONE
    cluster_ipv4_cidr     = Column(String, default="/17")               # clusterIpv4Cidr
    services_ipv4_cidr    = Column(String, default="/20")               # servicesIpv4Cidr
    enable_private_nodes  = Column(Boolean, default=False)              # privateClusterConfig
    logging_service       = Column(String, default="logging.googleapis.com/kubernetes")
    monitoring_service    = Column(String, default="monitoring.googleapis.com/kubernetes")
    binary_authorization  = Column(String, default="DISABLED")          # binaryAuthorization.evaluationMode
    api_server_port       = Column(Integer)                             # host port for multi-cluster kubectl
    certificate_authority = Column(String)                              # base64 CA cert
    resource_labels       = Column(JSON, default=dict)                  # GCP resource labels
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GKENodePool(Base):
    """GKE Node Pool within a cluster"""
    __tablename__ = "gke_node_pools"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String, nullable=False)
    cluster_name = Column(String, nullable=False)             # FK → gke_clusters.name
    project_id   = Column(String, nullable=False)
    location     = Column(String, nullable=False)
    status       = Column(String, default="PROVISIONING")     # same states as cluster
    node_count   = Column(Integer, default=3)
    machine_type = Column(String, default="e2-medium")
    disk_size_gb = Column(Integer, default=100)
    container_ids = Column(JSON, default=list)
    # ── GCP-aligned fields (Sprint 2) ──
    min_node_count         = Column(Integer, default=1)       # autoscaling.minNodeCount
    max_node_count         = Column(Integer, default=3)       # autoscaling.maxNodeCount
    autoscaling_enabled    = Column(Boolean, default=False)   # autoscaling.enabled
    preemptible            = Column(Boolean, default=False)   # config.preemptible
    spot                   = Column(Boolean, default=False)   # config.spot
    image_type             = Column(String, default="COS_CONTAINERD")  # config.imageType
    management_auto_repair  = Column(Boolean, default=True)   # management.autoRepair
    management_auto_upgrade = Column(Boolean, default=True)   # management.autoUpgrade
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GKEAddon(Base):
    """GKE Addon installed on a cluster (vpc-cni, HttpLoadBalancing, etc.)"""
    __tablename__ = "gke_addons"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(String, nullable=False)           # e.g. HttpLoadBalancing
    cluster_name   = Column(String, nullable=False)
    project_id     = Column(String, nullable=False)
    location       = Column(String, nullable=False)
    status         = Column(String, default="ENABLED")        # ENABLED | DISABLED
    version        = Column(String, default="")
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create any missing tables (new models)
Base.metadata.create_all(engine)


def _run_migrations() -> None:
    """Add columns introduced in Sprint 2 to pre-existing tables.
    Safe to run multiple times — silently skips columns that already exist.
    """
    new_cluster_cols = [
        ("cluster_type",         "VARCHAR DEFAULT 'STANDARD'"),
        ("release_channel",      "VARCHAR DEFAULT 'REGULAR'"),
        ("cluster_ipv4_cidr",    "VARCHAR DEFAULT '/17'"),
        ("services_ipv4_cidr",   "VARCHAR DEFAULT '/20'"),
        ("enable_private_nodes", "BOOLEAN DEFAULT 0"),
        ("logging_service",      "VARCHAR DEFAULT 'logging.googleapis.com/kubernetes'"),
        ("monitoring_service",   "VARCHAR DEFAULT 'monitoring.googleapis.com/kubernetes'"),
        ("binary_authorization", "VARCHAR DEFAULT 'DISABLED'"),
        ("api_server_port",      "INTEGER"),
        ("certificate_authority","VARCHAR"),
        ("resource_labels",      "JSON DEFAULT '{}'"),
    ]
    new_nodepool_cols = [
        ("min_node_count",          "INTEGER DEFAULT 1"),
        ("max_node_count",          "INTEGER DEFAULT 3"),
        ("autoscaling_enabled",     "BOOLEAN DEFAULT 0"),
        ("preemptible",             "BOOLEAN DEFAULT 0"),
        ("spot",                    "BOOLEAN DEFAULT 0"),
        ("image_type",              "VARCHAR DEFAULT 'COS_CONTAINERD'"),
        ("management_auto_repair",  "BOOLEAN DEFAULT 1"),
        ("management_auto_upgrade", "BOOLEAN DEFAULT 1"),
    ]
    with engine.connect() as conn:
        for col, typ in new_cluster_cols:
            try:
                conn.execute(text(f"ALTER TABLE gke_clusters ADD COLUMN {col} {typ}"))
                conn.commit()
            except Exception:
                pass
        for col, typ in new_nodepool_cols:
            try:
                conn.execute(text(f"ALTER TABLE gke_node_pools ADD COLUMN {col} {typ}"))
                conn.commit()
            except Exception:
                pass


_run_migrations()

def get_db():
    """Database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
