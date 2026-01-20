"""
Migration 016: Add Cloud Router and Cloud NAT tables

Cloud Router enables dynamic route exchange via BGP.
Cloud NAT allows instances without external IPs to access the internet.

Tables:
- routers: Cloud Router configurations
- cloud_nat: Cloud NAT configurations attached to routers
"""

from app.factory import db


def upgrade():
    """Apply migration: Create routers and cloud_nat tables"""
    
    # Create routers table
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS routers (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(63) NOT NULL,
            network_id VARCHAR(36) NOT NULL REFERENCES networks(id) ON DELETE CASCADE,
            region VARCHAR(50) NOT NULL,
            description TEXT,
            bgp_asn INTEGER NOT NULL,
            bgp_keepalive_interval INTEGER DEFAULT 20,
            creation_timestamp TIMESTAMP DEFAULT NOW(),
            CONSTRAINT unique_router_per_region UNIQUE (network_id, region, name)
        );
    """)
    
    # Create indexes for routers
    db.session.execute("""
        CREATE INDEX IF NOT EXISTS idx_routers_network_id ON routers(network_id);
    """)
    
    db.session.execute("""
        CREATE INDEX IF NOT EXISTS idx_routers_region ON routers(region);
    """)
    
    # Create cloud_nat table
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS cloud_nat (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(63) NOT NULL,
            router_id VARCHAR(36) NOT NULL REFERENCES routers(id) ON DELETE CASCADE,
            nat_ip_allocate_option VARCHAR(50) DEFAULT 'AUTO_ONLY',
            source_subnetwork_ip_ranges_to_nat VARCHAR(50) DEFAULT 'ALL_SUBNETWORKS_ALL_IP_RANGES',
            nat_ips JSON DEFAULT '[]',
            min_ports_per_vm INTEGER DEFAULT 64,
            max_ports_per_vm INTEGER DEFAULT 65536,
            enable_logging BOOLEAN DEFAULT FALSE,
            log_filter VARCHAR(50) DEFAULT 'ALL',
            creation_timestamp TIMESTAMP DEFAULT NOW(),
            CONSTRAINT unique_nat_per_router UNIQUE (router_id, name)
        );
    """)
    
    # Create indexes for cloud_nat
    db.session.execute("""
        CREATE INDEX IF NOT EXISTS idx_cloud_nat_router_id ON cloud_nat(router_id);
    """)
    
    db.session.commit()
    print("✅ Migration 016: Created routers and cloud_nat tables")


def downgrade():
    """Rollback migration: Drop routers and cloud_nat tables"""
    
    db.session.execute("DROP TABLE IF EXISTS cloud_nat CASCADE;")
    db.session.execute("DROP TABLE IF EXISTS routers CASCADE;")
    db.session.commit()
    print("✅ Migration 016 rollback: Dropped routers and cloud_nat tables")


if __name__ == "__main__":
    from app.factory import create_app
    app = create_app()
    
    with app.app_context():
        print("Running migration 016: Add Cloud Router and Cloud NAT...")
        upgrade()
        print("Migration 016 complete!")
