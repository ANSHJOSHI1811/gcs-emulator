"""
Migration 006: Add VPC tables (Network, Subnetwork, NetworkInterface)
Phase 1: Control plane network identity and fake IP allocation
"""
from sqlalchemy import text


def upgrade(db):
    """Create VPC tables"""
    
    # Create networks table
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS networks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(63) NOT NULL,
            project_id VARCHAR(255) NOT NULL,
            description TEXT,
            auto_create_subnetworks BOOLEAN NOT NULL DEFAULT FALSE,
            routing_mode VARCHAR(20) DEFAULT 'REGIONAL',
            mtu INTEGER DEFAULT 1460,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, name)
        )
    """))
    
    # Create index on project_id for faster lookups
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_networks_project_id ON networks(project_id)
    """))
    
    # Create subnetworks table
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS subnetworks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(63) NOT NULL,
            network_id INTEGER NOT NULL REFERENCES networks(id) ON DELETE CASCADE,
            region VARCHAR(50) NOT NULL,
            ip_cidr_range VARCHAR(50) NOT NULL,
            gateway_address VARCHAR(45),
            description TEXT,
            private_ip_google_access BOOLEAN DEFAULT FALSE,
            next_ip_index INTEGER DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(network_id, name)
        )
    """))
    
    # Create indexes for subnetworks
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_subnetworks_network_id ON subnetworks(network_id)
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_subnetworks_region ON subnetworks(region)
    """))
    
    # Create network_interfaces table
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS network_interfaces (
            id SERIAL PRIMARY KEY,
            instance_id INTEGER NOT NULL REFERENCES instances(id) ON DELETE CASCADE,
            network_id INTEGER NOT NULL REFERENCES networks(id) ON DELETE CASCADE,
            subnetwork_id INTEGER NOT NULL REFERENCES subnetworks(id) ON DELETE CASCADE,
            network_ip VARCHAR(45) NOT NULL,
            name VARCHAR(63) DEFAULT 'nic0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(instance_id, name)
        )
    """))
    
    # Create indexes for network_interfaces
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_network_interfaces_instance_id ON network_interfaces(instance_id)
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_network_interfaces_network_id ON network_interfaces(network_id)
    """))
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_network_interfaces_subnetwork_id ON network_interfaces(subnetwork_id)
    """))
    
    db.commit()
    print("✅ Migration 006: VPC tables created successfully")


def downgrade(db):
    """Drop VPC tables"""
    db.execute(text("DROP TABLE IF EXISTS network_interfaces CASCADE"))
    db.execute(text("DROP TABLE IF EXISTS subnetworks CASCADE"))
    db.execute(text("DROP TABLE IF EXISTS networks CASCADE"))
    db.commit()
    print("✅ Migration 006: VPC tables dropped")


if __name__ == '__main__':
    from app.factory import create_app, db
    app = create_app()
    with app.app_context():
        upgrade(db.session)
