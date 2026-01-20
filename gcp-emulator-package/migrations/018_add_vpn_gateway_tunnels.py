"""
Migration 018: Add VPN Gateway and Tunnel support

Creates vpn_gateways and vpn_tunnels tables.
"""

from app.factory import create_app, db
from sqlalchemy import text


def upgrade():
    """Create VPN tables"""
    connection = db.engine.connect()
    trans = connection.begin()
    
    try:
        # Create vpn_gateways table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS vpn_gateways (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(63) NOT NULL,
                project_id VARCHAR(255) NOT NULL,
                region VARCHAR(50) NOT NULL,
                network_id UUID REFERENCES networks(id) ON DELETE CASCADE,
                description TEXT,
                vpn_gateway_type VARCHAR(20) DEFAULT 'CLASSIC',
                vpn_interface_0_ip_address VARCHAR(50),
                vpn_interface_1_ip_address VARCHAR(50),
                status VARCHAR(20) DEFAULT 'READY',
                creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, region, name)
            )
        """))
        
        # Create vpn_tunnels table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS vpn_tunnels (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(63) NOT NULL,
                project_id VARCHAR(255) NOT NULL,
                region VARCHAR(50) NOT NULL,
                vpn_gateway_id VARCHAR(36) REFERENCES vpn_gateways(id) ON DELETE CASCADE,
                peer_ip VARCHAR(50) NOT NULL,
                peer_external_gateway VARCHAR(255),
                router_id VARCHAR(36) REFERENCES routers(id) ON DELETE SET NULL,
                ike_version INTEGER DEFAULT 2,
                shared_secret VARCHAR(255) NOT NULL,
                local_traffic_selector JSON DEFAULT '[]',
                remote_traffic_selector JSON DEFAULT '[]',
                description TEXT,
                status VARCHAR(20) DEFAULT 'ESTABLISHED',
                detailed_status TEXT,
                creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, region, name)
            )
        """))
        
        # Create indexes
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_vpn_gateways_project_region 
            ON vpn_gateways(project_id, region)
        """))
        
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_vpn_gateways_network_id 
            ON vpn_gateways(network_id)
        """))
        
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_vpn_tunnels_project_region 
            ON vpn_tunnels(project_id, region)
        """))
        
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_vpn_tunnels_gateway_id 
            ON vpn_tunnels(vpn_gateway_id)
        """))
        
        trans.commit()
        print("✅ Migration 018: VPN Gateway and Tunnel tables created successfully")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Migration 018 failed: {str(e)}")
        raise


def downgrade():
    """Drop VPN tables"""
    connection = db.engine.connect()
    trans = connection.begin()
    
    try:
        connection.execute(text("DROP TABLE IF EXISTS vpn_tunnels CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS vpn_gateways CASCADE"))
        trans.commit()
        print("✅ Migration 018: VPN tables dropped")
        
    except Exception as e:
        trans.rollback()
        print(f"❌ Migration 018 downgrade failed: {str(e)}")
        raise


if __name__ == "__main__":
    print("Running Migration 018: Add VPN Gateway and Tunnels...")
    app = create_app()
    with app.app_context():
        upgrade()
