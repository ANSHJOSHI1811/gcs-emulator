"""Migration script to add CIDR support to database"""
from database import Base, engine, SessionLocal, Network, Subnet
from sqlalchemy import text
from datetime import datetime
import uuid

print("Starting database migration for CIDR support...")

# Drop tables in correct order (respect foreign keys)
with engine.connect() as conn:
    print("Dropping existing tables...")
    conn.execute(text("DROP TABLE IF EXISTS instances CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS subnets CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS networks CASCADE"))
    conn.commit()
    print("✓ Tables dropped")

# Recreate all tables
print("Recreating tables with CIDR support...")
Base.metadata.create_all(engine)
print("✓ Tables recreated")

# Create default network and subnet
print("Creating default network and subnet...")
db = SessionLocal()

try:
    # Default network
    default_net = Network(
        id=1,
        name="default",
        project_id="default",
        docker_network_name="gcp-default",
        auto_create_subnetworks=True
    )
    db.add(default_net)
    
    # Default subnet
    default_subnet = Subnet(
        id=str(uuid.uuid4()),
        name="default",
        network="default",
        region="us-central1",
        ip_cidr_range="10.128.0.0/20",
        gateway_ip="10.128.0.1",
        next_available_ip=2
    )
    db.add(default_subnet)
    
    db.commit()
    print("✓ Default network: 10.128.0.0/20")
    print("✓ Default subnet: 10.128.0.0/20, gateway 10.128.0.1")
    
except Exception as e:
    db.rollback()
    print(f"✗ Error creating defaults: {e}")
finally:
    db.close()

print("\n✅ Migration complete!")
print("Run verification:")
print("  psql -U postgres -h database-1.cxeqkmcg8wj2.eu-north-1.rds.amazonaws.com gcs_stimulator -c 'SELECT name FROM networks;'")
print("  psql -U postgres -h database-1.cxeqkmcg8wj2.eu-north-1.rds.amazonaws.com gcs_stimulator -c 'SELECT name, ip_cidr_range, gateway_ip FROM subnets;'")
