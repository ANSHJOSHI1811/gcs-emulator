"""
Migration 005 - Add IAM and Compute Engine tables
"""
from app.factory import create_app, db
from app.models import (
    ServiceAccount, ServiceAccountKey, 
    IamPolicy, Role,
    Instance, Zone, MachineType
)


def upgrade():
    """Add IAM and Compute tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating IAM and Compute Engine tables...")
        
        # Create all tables
        db.create_all()
        
        # Add default zones
        zones_data = [
            {"id": "us-central1-a", "name": "us-central1-a", "region": "us-central1", "status": "UP", "description": "US Central Iowa zone A"},
            {"id": "us-central1-b", "name": "us-central1-b", "region": "us-central1", "status": "UP", "description": "US Central Iowa zone B"},
            {"id": "us-east1-a", "name": "us-east1-a", "region": "us-east1", "status": "UP", "description": "US East South Carolina zone A"},
            {"id": "us-west1-a", "name": "us-west1-a", "region": "us-west1", "status": "UP", "description": "US West Oregon zone A"},
            {"id": "europe-west1-a", "name": "europe-west1-a", "region": "europe-west1", "status": "UP", "description": "Europe West Belgium zone A"},
            {"id": "asia-east1-a", "name": "asia-east1-a", "region": "asia-east1", "status": "UP", "description": "Asia East Taiwan zone A"},
        ]
        
        for zone_data in zones_data:
            zone = Zone.query.filter_by(id=zone_data["id"]).first()
            if not zone:
                zone = Zone(**zone_data)
                db.session.add(zone)
        
        # Add default machine types for each zone
        machine_types = [
            {"name": "e2-micro", "guest_cpus": 1, "memory_mb": 1024, "is_shared_cpu": True, "description": "2 vCPUs, 1 GB RAM"},
            {"name": "e2-small", "guest_cpus": 2, "memory_mb": 2048, "is_shared_cpu": True, "description": "2 vCPUs, 2 GB RAM"},
            {"name": "e2-medium", "guest_cpus": 2, "memory_mb": 4096, "is_shared_cpu": True, "description": "2 vCPUs, 4 GB RAM"},
            {"name": "n1-standard-1", "guest_cpus": 1, "memory_mb": 3840, "is_shared_cpu": False, "description": "1 vCPU, 3.75 GB RAM"},
            {"name": "n1-standard-2", "guest_cpus": 2, "memory_mb": 7680, "is_shared_cpu": False, "description": "2 vCPUs, 7.5 GB RAM"},
            {"name": "n1-standard-4", "guest_cpus": 4, "memory_mb": 15360, "is_shared_cpu": False, "description": "4 vCPUs, 15 GB RAM"},
        ]
        
        for zone_data in zones_data:
            zone_id = zone_data["id"]
            for mt_data in machine_types:
                mt_id = f"{zone_id}/{mt_data['name']}"
                existing = MachineType.query.filter_by(id=mt_id).first()
                if not existing:
                    mt = MachineType(
                        id=mt_id,
                        name=mt_data["name"],
                        zone=zone_id,
                        guest_cpus=mt_data["guest_cpus"],
                        memory_mb=mt_data["memory_mb"],
                        is_shared_cpu=mt_data["is_shared_cpu"],
                        description=mt_data["description"],
                    )
                    db.session.add(mt)
        
        # Add default predefined roles
        predefined_roles = [
            {
                "id": "roles/owner",
                "name": "roles/owner",
                "title": "Owner",
                "description": "Full access to all resources",
                "permissions": ["storage.buckets.*", "storage.objects.*", "compute.instances.*", "iam.serviceAccounts.*"],
            },
            {
                "id": "roles/editor",
                "name": "roles/editor",
                "title": "Editor",
                "description": "Edit access to all resources",
                "permissions": ["storage.buckets.create", "storage.objects.*", "compute.instances.*"],
            },
            {
                "id": "roles/viewer",
                "name": "roles/viewer",
                "title": "Viewer",
                "description": "Read-only access to all resources",
                "permissions": ["storage.buckets.get", "storage.objects.get", "compute.instances.get"],
            },
            {
                "id": "roles/storage.admin",
                "name": "roles/storage.admin",
                "title": "Storage Admin",
                "description": "Full control of GCS resources",
                "permissions": ["storage.buckets.*", "storage.objects.*"],
            },
            {
                "id": "roles/compute.admin",
                "name": "roles/compute.admin",
                "title": "Compute Admin",
                "description": "Full control of Compute Engine resources",
                "permissions": ["compute.instances.*", "compute.zones.*", "compute.machineTypes.*"],
            },
        ]
        
        for role_data in predefined_roles:
            role = Role.query.filter_by(id=role_data["id"]).first()
            if not role:
                role = Role(**role_data)
                db.session.add(role)
        
        db.session.commit()
        
        print("✅ IAM and Compute Engine tables created successfully!")
        print(f"   - Created {len(zones_data)} zones")
        print(f"   - Created {len(zones_data) * len(machine_types)} machine types")
        print(f"   - Created {len(predefined_roles)} predefined roles")


def downgrade():
    """Remove IAM and Compute tables"""
    app = create_app()
    
    with app.app_context():
        print("Dropping IAM and Compute Engine tables...")
        
        # Drop tables
        MachineType.__table__.drop(db.engine, checkfirst=True)
        Instance.__table__.drop(db.engine, checkfirst=True)
        Zone.__table__.drop(db.engine, checkfirst=True)
        ServiceAccountKey.__table__.drop(db.engine, checkfirst=True)
        ServiceAccount.__table__.drop(db.engine, checkfirst=True)
        Role.__table__.drop(db.engine, checkfirst=True)
        IamPolicy.__table__.drop(db.engine, checkfirst=True)
        
        print("✅ IAM and Compute Engine tables dropped successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
