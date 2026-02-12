#!/usr/bin/env python3
"""Sync existing Docker containers (gcp-vm-*) to database as instances"""
import docker
from database import SessionLocal, Instance, Project, Network
import re
from datetime import datetime

def sync_docker_instances():
    """Find all gcp-vm-* containers and register them as instances"""
    client = docker.from_env()
    db = SessionLocal()
    
    try:
        # Get all containers (including stopped)
        containers = client.containers.list(all=True, filters={"name": "gcp-vm-"})
        
        print(f"Found {len(containers)} Docker containers with 'gcp-vm-' prefix")
        
        # Get all projects
        projects = db.query(Project).all()
        if not projects:
            print("⚠️  No projects found. Please create a project first.")
            return
        
        # Get all networks
        networks = db.query(Network).all()
        network_map = {n.docker_network_name: n for n in networks}
        
        synced_count = 0
        for container in containers:
            container_name = container.name
            container_id = container.id
            
            # Check if already in database
            existing = db.query(Instance).filter_by(container_id=container_id).first()
            if existing:
                print(f"  ⏭️  {container_name} already in database")
                continue
            
            # Extract instance name from container name (gcp-vm-{name})
            instance_name = container_name.replace("gcp-vm-", "")
            
            # Get container status
            status = "RUNNING" if container.status == "running" else "TERMINATED"
            
            # Get network information
            networks_data = container.attrs.get('NetworkSettings', {}).get('Networks', {})
            internal_ip = None
            network_url = "global/networks/default"
            
            # Try to find IP and network
            for net_name, net_info in networks_data.items():
                internal_ip = net_info.get('IPAddress')
                if internal_ip:
                    # Try to find matching network in DB
                    if net_name in network_map:
                        network = network_map[net_name]
                        network_url = f"global/networks/{network.name}"
                    break
            
            # Guess project based on container name patterns
            # Look for project names in container name
            project_id = None
            for project in projects:
                if project.id in container_name or project.name.lower().replace(" ", "-") in container_name:
                    project_id = project.id
                    break
            
            # If no project matched, use first project
            if not project_id:
                project_id = projects[0].id
                print(f"  ⚠️  Couldn't determine project for {container_name}, using {project_id}")
            
            # Default zone
            zone = "us-central1-a"
            
            # Create instance record
            instance = Instance(
                name=instance_name,
                project_id=project_id,
                zone=zone,
                machine_type="n1-standard-1",
                status=status,
                container_id=container_id,
                container_name=container_name,
                internal_ip=internal_ip or "10.128.0.10",
                external_ip=None,  # No external IP for existing containers
                network_url=network_url,
                subnet="default",
                source_image="ubuntu-22-04",
                disk_size_gb=10,
                created_at=datetime.utcnow()
            )
            
            db.add(instance)
            synced_count += 1
            print(f"  ✅ Synced: {container_name} -> {project_id}/{zone}/{instance_name}")
        
        db.commit()
        print(f"\n✅ Successfully synced {synced_count} containers to database")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_docker_instances()
