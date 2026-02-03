"""Database models and connection"""
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean, Integer
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
    
    id = Column(String, primary_key=True)
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
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    project_id = Column(String, nullable=False)
    description = Column(String)
    auto_create_subnetworks = Column(Boolean, default=True)
    routing_mode = Column(String, default="REGIONAL")
    docker_network_id = Column(String)  # Docker network ID
    docker_network_name = Column(String)  # Docker network name
    creation_timestamp = Column(DateTime, default=datetime.utcnow)

# Don't create tables - they already exist in RDS
# Base.metadata.create_all(engine)

def get_db():
    """Database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
