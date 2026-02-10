"""Database models and connection"""
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean, Integer, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345678@database-1.cxeqkmcg8wj2.eu-north-1.rds.amazonaws.com:5432/gcs_stimulator")

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
    route_table_id = Column(Integer)  # Reference to route table (nullable for backward compat)
    created_at = Column(DateTime, default=datetime.utcnow)


class RouteTable(Base):
    """Route Table for managing routes"""
    __tablename__ = "route_tables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    project_id = Column(String, nullable=False)
    network = Column(String, nullable=False)  # Network reference
    description = Column(String)
    is_default = Column(Boolean, default=False)  # Auto-created default table
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SubnetRouteTableAssociation(Base):
    """Association between subnet and route table"""
    __tablename__ = "subnet_route_table_associations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subnet_name = Column(String, nullable=False)
    route_table_id = Column(Integer, nullable=False)
    project_id = Column(String, nullable=False)
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


# Create any missing tables (new models)
Base.metadata.create_all(engine)

def get_db():
    """Database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
